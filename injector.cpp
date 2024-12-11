#include <windows.h>
#include <iostream>
#include <string>
#include <iomanip>  // for std::hex

bool InjectDLL(DWORD processID, const char* dllPath) {
    HANDLE hProcess = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_VM_READ, FALSE, processID);
    if (!hProcess) {
        std::cerr << "Failed to open process: " << GetLastError() << std::endl;
        return false;
    }
    std::cout << "Process handle: 0x" << std::hex << (uintptr_t)hProcess << std::dec << std::endl;

    size_t pathLen = strlen(dllPath) + 1;
    LPVOID pDllPath = VirtualAllocEx(hProcess, nullptr, pathLen, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!pDllPath) {
        std::cerr << "Failed to allocate memory in target process: " << GetLastError() << std::endl;
        CloseHandle(hProcess);
        return false;
    }
    std::cout << "Allocated memory address: 0x" << std::hex << (uintptr_t)pDllPath << std::dec << std::endl;

    if (!WriteProcessMemory(hProcess, pDllPath, dllPath, pathLen, nullptr)) {
        std::cerr << "Failed to write DLL path into target process: " << GetLastError() << std::endl;
        VirtualFreeEx(hProcess, pDllPath, 0, MEM_RELEASE);
        CloseHandle(hProcess);
        return false;
    }
    std::cout << "DLL path written to memory: " << dllPath << std::endl;

    HMODULE hKernel32 = GetModuleHandleA("kernel32.dll");
    if (!hKernel32) {
        std::cerr << "Failed to get handle for kernel32.dll: " << GetLastError() << std::endl;
        VirtualFreeEx(hProcess, pDllPath, 0, MEM_RELEASE);
        CloseHandle(hProcess);
        return false;
    }
    std::cout << "Kernel32 handle: 0x" << std::hex << (uintptr_t)hKernel32 << std::dec << std::endl;

    LPTHREAD_START_ROUTINE loadLibrary = (LPTHREAD_START_ROUTINE)GetProcAddress(hKernel32, "LoadLibraryA");
    if (!loadLibrary) {
        std::cerr << "Failed to get LoadLibraryA address: " << GetLastError() << std::endl;
        VirtualFreeEx(hProcess, pDllPath, 0, MEM_RELEASE);
        CloseHandle(hProcess);
        return false;
    }
    std::cout << "LoadLibraryA address: 0x" << std::hex << (uintptr_t)loadLibrary << std::dec << std::endl;

    HANDLE hThread = CreateRemoteThread(hProcess, nullptr, 0, loadLibrary, pDllPath, 0, nullptr);
    if (!hThread) {
        std::cerr << "Failed to create remote thread: " << GetLastError() << std::endl;
        VirtualFreeEx(hProcess, pDllPath, 0, MEM_RELEASE);
        CloseHandle(hProcess);
        return false;
    }
    std::cout << "Remote thread handle: 0x" << std::hex << (uintptr_t)hThread << std::dec << std::endl;

    DWORD waitResult = WaitForSingleObject(hThread, INFINITE);
    if (waitResult == WAIT_FAILED) {
        std::cerr << "WaitForSingleObject failed: " << GetLastError() << std::endl;
    } else {
        DWORD exitCode;
        GetExitCodeThread(hThread, &exitCode);
        std::cout << "Remote thread finished. Exit code: 0x" << std::hex << exitCode << std::dec << std::endl;
    }

    VirtualFreeEx(hProcess, pDllPath, 0, MEM_RELEASE);
    CloseHandle(hThread);
    CloseHandle(hProcess);

    return true;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <PID> <DLL Path>" << std::endl;
        return 1;
    }

    DWORD processID = std::stoul(argv[1]);
    const char* dllPath = argv[2];

    if (InjectDLL(processID, dllPath)) {
        std::cout << "DLL injection attempted." << std::endl;
    } else {
        std::cerr << "DLL injection failed." << std::endl;
    }

    return 0;
}