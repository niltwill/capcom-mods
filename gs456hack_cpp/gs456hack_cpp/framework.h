#pragma once

#ifdef _WIN64
#define _AMD64_
#else
#define _X86_
#endif

#define WIN32_LEAN_AND_MEAN // Exclude rarely-used stuff from Windows headers
#define EXTERN_API extern "C" _declspec(dllexport)

// Function typedef
#define __typedef_func(func, ret, ...) using func##_t = ret(WINAPI*)(##__VA_ARGS__); func##_t m_##func = nullptr;
#define __typedef_func_winapi(func, ret, ...) using func##_t = ret(WINAPI*)(##__VA_ARGS__); func##_t m_##func = func##;

// Resolve the specified function proc
#define __setup_proc(func, proxy) m_##func = reinterpret_cast<func##_t>(::GetProcAddress(##proxy, #func));

// Set the proc back to nullptr
#define __clear_proc(func) if(m_##func) m_##func = nullptr;

// Windows header files
#include <minwindef.h>
#include <libloaderapi.h>
#include <sysinfoapi.h>
#include <profileapi.h>
#include <winternl.h>
#include <processthreadsapi.h>
#include <timeapi.h>
#include <tlhelp32.h>
#include <Xinput.h>
#include <iostream>
#include <string>
#include <fstream>
#include <filesystem>
#include <chrono> 
#include <thread>
#include <map>
#include <set>
#include <unordered_map>
#include <unordered_set>
#include <sstream>
#include "handleapi.h"
#include "errhandlingapi.h"
#include "memoryapi.h"
#include "stringapiset.h"
#include "winuser.h"
#include "psapi.h"
#include "winerror.h"

// Proxy stub
#include "stub.h"

// This project itself
#include "gs456hack.h"