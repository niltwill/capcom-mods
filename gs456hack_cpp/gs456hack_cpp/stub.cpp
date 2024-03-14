#include "pch.h"

#pragma region DINPUT8_DLL

EXTERN_API HRESULT WINAPI DirectInput8Create(
    HINSTANCE hinst,
    DWORD dwVersion,
    REFIID riidltf,
    LPVOID* ppvOut,
    void* punkOuter
)
{
    return CProxyStub::instance().m_DirectInput8Create(hinst, dwVersion, riidltf, ppvOut, punkOuter);
}

EXTERN_API HRESULT WINAPI DllCanUnloadNow()
{
    return CProxyStub::instance().m_DllCanUnloadNow();
}

EXTERN_API HRESULT WINAPI DllGetClassObject(
    const CLSID& rclsid,
    const IID& riid,
    void** ppv
)
{
    return CProxyStub::instance().m_DllGetClassObject(rclsid, riid, ppv);
}

EXTERN_API HRESULT WINAPI DllRegisterServer()
{
    return CProxyStub::instance().m_DllRegisterServer();
}

EXTERN_API HRESULT WINAPI DllUnregisterServer()
{
    return CProxyStub::instance().m_DllUnregisterServer();
}

EXTERN_API HRESULT WINAPI GetdfDIJoystick()
{
    return CProxyStub::instance().m_GetdfDIJoystick();
}

#pragma endregion

/*
#pragma region VERSION_DLL

EXTERN_API BOOL WINAPI GetFileVersionInfoA(
     LPCSTR lptstrFilename,
     DWORD dwHandle,
     DWORD dwLen,
     LPVOID lpData
)
{
    return CProxyStub::instance().m_GetFileVersionInfoA(lptstrFilename, dwHandle, dwLen, lpData);
}


EXTERN_API BOOL WINAPI GetFileVersionInfoByHandle(
    size_t aUnkn1,
    HANDLE hFile,
    size_t aUnkn3,
    size_t aUnkn4
)
{
    return CProxyStub::instance().m_GetFileVersionInfoByHandle(aUnkn1, hFile, aUnkn3, aUnkn4);
}


EXTERN_API BOOL WINAPI GetFileVersionInfoExA(
  DWORD dwFlags,
  LPCSTR lpwstrFilename,
  DWORD dwHandle,
  DWORD dwLen,
  LPVOID lpData
)
{
    return CProxyStub::instance().m_GetFileVersionInfoExA(dwFlags, lpwstrFilename, dwHandle, dwLen, lpData);
}


EXTERN_API BOOL WINAPI GetFileVersionInfoExW(
    DWORD dwFlags,
    LPCWSTR lpwstrFilename,
    DWORD dwHandle,
    DWORD dwLen,
    LPVOID lpData
)
{
    return CProxyStub::instance().m_GetFileVersionInfoExW(dwFlags, lpwstrFilename, dwHandle, dwLen, lpData);
}


EXTERN_API DWORD WINAPI GetFileVersionInfoSizeA(
    LPCSTR lptstrFilename,
    LPDWORD lpdwHandle
)
{
    return CProxyStub::instance().m_GetFileVersionInfoSizeA(lptstrFilename, lpdwHandle);
}


EXTERN_API DWORD WINAPI GetFileVersionInfoSizeExA(
    DWORD dwFlags,
    LPCSTR lpwstrFilename,
    LPDWORD lpdwHandle
)
{
    return CProxyStub::instance().m_GetFileVersionInfoSizeExA(dwFlags, lpwstrFilename, lpdwHandle);
}


EXTERN_API DWORD WINAPI GetFileVersionInfoSizeExW(
    DWORD dwFlags,
    LPCWSTR lpwstrFilename,
    LPDWORD lpdwHandle
)
{
    return CProxyStub::instance().m_GetFileVersionInfoSizeExW(dwFlags, lpwstrFilename, lpdwHandle);
}


EXTERN_API DWORD WINAPI GetFileVersionInfoSizeW(
    LPCWSTR lptstrFilename,
    LPDWORD lpdwHandle
)
{
    return CProxyStub::instance().m_GetFileVersionInfoSizeW(lptstrFilename, lpdwHandle);
}


EXTERN_API BOOL WINAPI GetFileVersionInfoW(
    LPCWSTR lptstrFilename,
    DWORD dwHandle,
    DWORD dwLen,
    LPVOID lpData
)
{
    return CProxyStub::instance().m_GetFileVersionInfoW(lptstrFilename, dwHandle, dwLen, lpData);
}


EXTERN_API DWORD WINAPI VerFindFileA(
    DWORD uFlags,
    LPCSTR szFileName,
    LPCSTR szWinDir,
    LPCSTR szAppDir,
    LPSTR szCurDir,
    PUINT lpuCurDirLen,
    LPSTR szDestDir,
    PUINT lpuDestDirLen
)
{
    return CProxyStub::instance().m_VerFindFileA(uFlags, szFileName, szWinDir, szAppDir, szCurDir, lpuCurDirLen,
        szDestDir, lpuDestDirLen);
}


EXTERN_API DWORD WINAPI VerFindFileW(
    DWORD uFlags,
    LPCWSTR szFileName,
    LPCWSTR szWinDir,
    LPCWSTR szAppDir,
    LPWSTR szCurDir,
    PUINT lpuCurDirLen,
    LPWSTR szDestDir,
    PUINT lpuDestDirLen
)
{
    return CProxyStub::instance().m_VerFindFileW(uFlags, szFileName, szWinDir, szAppDir, szCurDir, lpuCurDirLen, szDestDir, lpuDestDirLen);
}


EXTERN_API DWORD WINAPI VerInstallFileA(
    DWORD uFlags,
    LPCSTR szSrcFileName,
    LPCSTR szDestFileName,
    LPCSTR szSrcDir,
    LPCSTR szDestDir,
    LPCSTR szCurDir,
    LPSTR szTmpFile,
    PUINT lpuTmpFileLen
)
{
    return CProxyStub::instance().m_VerInstallFileA(uFlags, szSrcFileName, szDestFileName, szSrcDir, szDestDir, szCurDir, szTmpFile, lpuTmpFileLen);
}


EXTERN_API DWORD WINAPI VerInstallFileW(
    DWORD uFlags,
    LPCWSTR szSrcFileName,
    LPCWSTR szDestFileName,
    LPCWSTR szSrcDir,
    LPCWSTR szDestDir,
    LPCWSTR szCurDir,
    LPWSTR szTmpFile,
    PUINT lpuTmpFileLen
)
{
    return CProxyStub::instance().m_VerInstallFileW(uFlags, szSrcFileName, szDestFileName, szSrcDir, szDestDir, szCurDir, szTmpFile, lpuTmpFileLen);
}


EXTERN_API DWORD WINAPI VerLanguageNameA(
    DWORD wLang,
    LPSTR szLang,
    DWORD cchLang
)
{
    return CProxyStub::instance().m_VerLanguageNameA(wLang, szLang, cchLang);
}


EXTERN_API DWORD WINAPI VerLanguageNameW(
    DWORD wLang,
    LPWSTR szLang,
    DWORD cchLang
)
{
    return CProxyStub::instance().m_VerLanguageNameW(wLang, szLang, cchLang);
}


EXTERN_API BOOL WINAPI VerQueryValueA(
    LPCVOID pBlock,
    LPCSTR lpSubBlock,
    LPVOID* lplpBuffer,
    PUINT puLen
)
{
    return CProxyStub::instance().m_VerQueryValueA(pBlock, lpSubBlock, lplpBuffer, puLen);
}


EXTERN_API BOOL WINAPI VerQueryValueW(
    LPCVOID pBlock,
    LPCWSTR lpSubBlock,
    LPVOID* lplpBuffer,
    PUINT puLen
)
{
    return CProxyStub::instance().m_VerQueryValueW(pBlock, lpSubBlock, lplpBuffer, puLen);
}

#pragma endregion
*/