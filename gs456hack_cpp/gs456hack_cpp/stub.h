#pragma once

namespace fs = std::filesystem;

class CProxyStub
{
protected:

    CProxyStub() {}
    ~CProxyStub()
    {
        // 'dinput8.dll'
        __clear_proc(DirectInput8Create);
        __clear_proc(DllCanUnloadNow);
        __clear_proc(DllGetClassObject);
        __clear_proc(DllRegisterServer);
        __clear_proc(DllUnregisterServer);
        __clear_proc(GetdfDIJoystick);
        
        // 'version.dll'
        /*
        __clear_proc(GetFileVersionInfoA);
        __clear_proc(GetFileVersionInfoByHandle);
        __clear_proc(GetFileVersionInfoExA);
        __clear_proc(GetFileVersionInfoExW);
        __clear_proc(GetFileVersionInfoSizeA);
        __clear_proc(GetFileVersionInfoSizeExA);
        __clear_proc(GetFileVersionInfoSizeExW);
        __clear_proc(GetFileVersionInfoSizeW);
        __clear_proc(GetFileVersionInfoW);
        __clear_proc(VerFindFileA);
        __clear_proc(VerFindFileW);
        __clear_proc(VerInstallFileA);
        __clear_proc(VerInstallFileW);
        __clear_proc(VerLanguageNameA);
        __clear_proc(VerLanguageNameW);
        __clear_proc(VerQueryValueA);
        __clear_proc(VerQueryValueW);
        */
    }

private:

    // A list of supported proxy libraries
    std::vector<std::wstring> m_supported_proxies
    {
        L"dinput8.dll"
        //L"version.dll"
    };

public:

    /// <summary>
    /// Gets the current 'CProxyStub' class instance
    /// </summary>
    static CProxyStub& instance()
    {
        static CProxyStub instance;
        return instance;
    }


    // A full path to the proxy library
    fs::path m_proxy_path{};

    // Resolve typedefs
    // 'dinput8.dll'
    __typedef_func(DirectInput8Create, HRESULT, HINSTANCE hinst, DWORD dwVersion, REFIID riidltf, LPVOID* ppvOut, void* punkOuter);
    __typedef_func(DllCanUnloadNow, HRESULT);
    __typedef_func(DllGetClassObject, HRESULT, const CLSID& rclsid, const IID& riid, void** ppv);
    __typedef_func(DllRegisterServer, HRESULT);
    __typedef_func(DllUnregisterServer, HRESULT);
    __typedef_func(GetdfDIJoystick, HRESULT);

    // 'version.dll'
    /*
    __typedef_func(GetFileVersionInfoA, BOOL, LPCSTR, DWORD, DWORD, LPVOID);
    __typedef_func(GetFileVersionInfoByHandle, BOOL, size_t, HANDLE, size_t, size_t);
    __typedef_func(GetFileVersionInfoExA, BOOL, DWORD, LPCSTR, DWORD, DWORD, LPVOID);
    __typedef_func(GetFileVersionInfoExW, BOOL, DWORD, LPCWSTR, DWORD, DWORD, LPVOID);
    __typedef_func(GetFileVersionInfoSizeA, DWORD, LPCSTR, LPDWORD);
    __typedef_func(GetFileVersionInfoSizeExA, DWORD, DWORD, LPCSTR, LPDWORD);
    __typedef_func(GetFileVersionInfoSizeExW, DWORD, DWORD, LPCWSTR, LPDWORD);
    __typedef_func(GetFileVersionInfoSizeW, DWORD, LPCWSTR, LPDWORD);
    __typedef_func(GetFileVersionInfoW, BOOL, LPCWSTR, DWORD, DWORD, LPVOID);
    __typedef_func(VerFindFileA, DWORD, DWORD, LPCSTR, LPCSTR, LPCSTR, LPSTR, PUINT, LPSTR, PUINT);
    __typedef_func(VerFindFileW, DWORD, DWORD, LPCWSTR, LPCWSTR, LPCWSTR, LPWSTR, PUINT, LPWSTR, PUINT);
    __typedef_func(VerInstallFileA, DWORD, DWORD, LPCSTR, LPCSTR, LPCSTR, LPCSTR, LPCSTR, LPSTR, PUINT);
    __typedef_func(VerInstallFileW, DWORD, DWORD, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, LPCWSTR, LPWSTR, PUINT);
    __typedef_func(VerLanguageNameA, DWORD, DWORD, LPSTR, DWORD);
    __typedef_func(VerLanguageNameW, DWORD, DWORD, LPWSTR, DWORD);
    __typedef_func(VerQueryValueA, BOOL, LPCVOID, LPCSTR, LPVOID*, PUINT);
    __typedef_func(VerQueryValueW, BOOL, LPCVOID, LPCWSTR, LPVOID*, PUINT);
    */

    /// <summary>
    /// Loads an original system library and resolves all the function procs
    /// </summary>
    /// <returns>Returns "true" upon success, "false" otherwise</returns>
    bool resolve(const HMODULE& mod)
    {
        wchar_t proxy_path[MAX_PATH]{};
        GetModuleFileNameW(mod, proxy_path, MAX_PATH);

        m_proxy_path = fs::path(proxy_path).parent_path();

        auto proxy_name = fs::path(proxy_path).filename();

        // Check if our proxy library name is supported
        const auto proxy_name_str = proxy_name.c_str();
        bool proxy_supported = std::any_of(m_supported_proxies.begin(), m_supported_proxies.end(),
            [proxy_name_str](const auto& proxy) {
                return _wcsnicmp(proxy_name_str, proxy.c_str(), proxy.size()) == 0;
            });

        if (!proxy_supported)
            return false;

        wchar_t sys_path[MAX_PATH]{};
        GetSystemDirectoryW(sys_path, MAX_PATH);

        // A full path to the original system library
        auto system_dll_path = fs::path(sys_path) / proxy_name;

        // Try loading an original system library
        auto proxy_dll = LoadLibraryExW(system_dll_path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);

        if (proxy_dll == nullptr)
            return false;

        // 'dinput8.dll'
        __setup_proc(DirectInput8Create, proxy_dll);
        __setup_proc(DllCanUnloadNow, proxy_dll);
        __setup_proc(DllGetClassObject, proxy_dll);
        __setup_proc(DllRegisterServer, proxy_dll);
        __setup_proc(DllUnregisterServer, proxy_dll);
        __setup_proc(GetdfDIJoystick, proxy_dll);

        // 'version.dll'
        /*
        __setup_proc(GetFileVersionInfoA, proxy_dll);
        __setup_proc(GetFileVersionInfoByHandle, proxy_dll);
        __setup_proc(GetFileVersionInfoExA, proxy_dll);
        __setup_proc(GetFileVersionInfoExW, proxy_dll);
        __setup_proc(GetFileVersionInfoSizeA, proxy_dll);
        __setup_proc(GetFileVersionInfoSizeExA, proxy_dll);
        __setup_proc(GetFileVersionInfoSizeExW, proxy_dll);
        __setup_proc(GetFileVersionInfoSizeW, proxy_dll);
        __setup_proc(GetFileVersionInfoW, proxy_dll);
        __setup_proc(VerFindFileA, proxy_dll);
        __setup_proc(VerFindFileW, proxy_dll);
        __setup_proc(VerInstallFileA, proxy_dll);
        __setup_proc(VerInstallFileW, proxy_dll);
        __setup_proc(VerLanguageNameA, proxy_dll);
        __setup_proc(VerLanguageNameW, proxy_dll);
        __setup_proc(VerQueryValueA, proxy_dll);
        __setup_proc(VerQueryValueW, proxy_dll);
        */

        return true;
    }
};