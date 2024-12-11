#include <windows.h>

// Function prototype
DWORD WINAPI KeepWindowActive(LPVOID lpParam);

// Structure to hold instance-specific data
typedef struct {
    HANDLE thread;
    BOOL running;
    DWORD processId;
    HWND targetWindow;
} InstanceData;

// Use a handle to store instance data
static DWORD g_tlsIndex = TLS_OUT_OF_INDEXES;

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved) {
    switch (reason) {
        case DLL_PROCESS_ATTACH: {
            // Allocate TLS index on first load
            if (g_tlsIndex == TLS_OUT_OF_INDEXES) {
                g_tlsIndex = TlsAlloc();
                if (g_tlsIndex == TLS_OUT_OF_INDEXES) {
                    return FALSE;
                }
            }

            // Allocate instance-specific data
            InstanceData* data = (InstanceData*)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(InstanceData));
            if (!data) {
                return FALSE;
            }

            data->running = TRUE;
            data->processId = GetCurrentProcessId();
            TlsSetValue(g_tlsIndex, data);

            Sleep(1000);  // Wait for process to stabilize
            
            // Pass instance data to thread
            data->thread = CreateThread(NULL, 0, KeepWindowActive, data, 0, NULL);
            if (data->thread == NULL) {
                HeapFree(GetProcessHeap(), 0, data);
                return FALSE;
            }
            Sleep(500);
            break;
        }

        case DLL_PROCESS_DETACH: {
            InstanceData* data = (InstanceData*)TlsGetValue(g_tlsIndex);
            if (data) {
                data->running = FALSE;
                if (data->thread) {
                    WaitForSingleObject(data->thread, 1000);
                    CloseHandle(data->thread);
                }
                HeapFree(GetProcessHeap(), 0, data);
            }

            if (lpReserved == NULL) {  // If DLL is being unloaded dynamically
                TlsFree(g_tlsIndex);
                g_tlsIndex = TLS_OUT_OF_INDEXES;
            }
            break;
        }
    }
    return TRUE;
}

// Callback function for EnumWindows
BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam) {
    InstanceData* data = (InstanceData*)lParam;
    DWORD windowPid;
    GetWindowThreadProcessId(hwnd, &windowPid);
    
    if (windowPid == data->processId) {
        data->targetWindow = hwnd;
        return FALSE; // Stop enumeration
    }
    return TRUE; // Continue enumeration
}

DWORD WINAPI KeepWindowActive(LPVOID lpParam) {
    InstanceData* data = (InstanceData*)lpParam;
    if (!data) return 1;

    // Wait for process to fully initialize
    Sleep(2000);
    
    // Find window belonging to our process
    while (data->running && data->targetWindow == NULL) {
        Sleep(1000);
        EnumWindows(EnumWindowsProc, (LPARAM)data);
    }
    
    if (data->targetWindow == NULL) {
        return 1;
    }
    
    while (data->running) {
        if (IsWindow(data->targetWindow)) {
            SetActiveWindow(data->targetWindow);
            PostMessage(data->targetWindow, WM_ACTIVATE, WA_ACTIVE, (LPARAM)data->targetWindow);
            PostMessage(data->targetWindow, WM_SETFOCUS, (WPARAM)data->targetWindow, 0);
        }
        Sleep(100);
    }
    return 0;
}