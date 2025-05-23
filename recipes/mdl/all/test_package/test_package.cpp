#include <iostream>
#include <mi/mdl_sdk.h>

// printf() format specifier for arguments of type LPTSTR (Windows only).
#ifdef MI_PLATFORM_WINDOWS
#ifdef UNICODE
#define FMT_LPTSTR "%ls"
#else // UNICODE
#define FMT_LPTSTR "%s"
#endif // UNICODE
#endif // MI_PLATFORM_WINDOWS

void *g_dso_handle = 0;

mi::neuraylib::INeuray *load_and_get_ineuray(const char *filename = 0) {
#ifdef MI_PLATFORM_WINDOWS
  if (!filename)
    filename = "libmdl_sdk.dll";
  void *handle = LoadLibraryA((LPSTR)filename);
  if (!handle) {
    LPTSTR buffer = 0;
    LPCTSTR message = TEXT("unknown failure");
    DWORD error_code = GetLastError();
    if (FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER |
                          FORMAT_MESSAGE_FROM_SYSTEM |
                          FORMAT_MESSAGE_IGNORE_INSERTS,
                      0, error_code, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                      (LPTSTR)&buffer, 0, 0))
      message = buffer;
    printf("Failed to load library (%u): " FMT_LPTSTR, error_code, message);
    if (buffer)
      LocalFree(buffer);
    return 0;
  }
  void *symbol = GetProcAddress((HMODULE)handle, "mi_factory");
  if (!symbol) {
    LPTSTR buffer = 0;
    LPCTSTR message = TEXT("unknown failure");
    DWORD error_code = GetLastError();
    if (FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER |
                          FORMAT_MESSAGE_FROM_SYSTEM |
                          FORMAT_MESSAGE_IGNORE_INSERTS,
                      0, error_code, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                      (LPTSTR)&buffer, 0, 0))
      message = buffer;
    printf("GetProcAddress error (%u): " FMT_LPTSTR, error_code, message);
    if (buffer)
      LocalFree(buffer);
    return 0;
  }
#else  // MI_PLATFORM_WINDOWS
  if (!filename)
    filename = "libmdl_sdk.so";
  void *handle = dlopen(filename, RTLD_LAZY);
  if (!handle) {
    printf("%s\n", dlerror());
    return 0;
  }
  void *symbol = dlsym(handle, "mi_factory");
  if (!symbol) {
    printf("%s\n", dlerror());
    return 0;
  }
#endif // MI_PLATFORM_WINDOWS
  g_dso_handle = handle;
  mi::neuraylib::INeuray *neuray =
      mi::neuraylib::mi_factory<mi::neuraylib::INeuray>(symbol);
  if (!neuray)
    return 0;

  return neuray;
}

// Unloads the neuray library.
bool unload() {
#ifdef MI_PLATFORM_WINDOWS
  int result = FreeLibrary((HMODULE)g_dso_handle);
  if (result == 0) {
    LPTSTR buffer = 0;
    LPCTSTR message = TEXT("unknown failure");
    DWORD error_code = GetLastError();
    if (FormatMessage(FORMAT_MESSAGE_ALLOCATE_BUFFER |
                          FORMAT_MESSAGE_FROM_SYSTEM |
                          FORMAT_MESSAGE_IGNORE_INSERTS,
                      0, error_code, MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                      (LPTSTR)&buffer, 0, 0))
      message = buffer;
    printf("Failed to unload library (%u): " FMT_LPTSTR, error_code, message);
    if (buffer)
      LocalFree(buffer);
    return false;
  }
  return true;
#else
  int result = dlclose(g_dso_handle);
  if (result != 0) {
    printf("%s\n", dlerror());
    return false;
  }
  return true;
#endif
}

int main() {
  std::cout << "PATH=" << std::getenv("PATH") << std::endl;
  // Initialize MDL SDK (implicit linking)
  mi::base::Handle<mi::neuraylib::INeuray> neuray(load_and_get_ineuray());
  neuray->start();
  if (neuray->get_status() != mi::neuraylib::INeuray::Status::STARTED) {
    std::cerr << "Failed to initialize MDL SDK" << std::endl;
    return 1;
  }
  std::cout << "Hello MDL SDK!" << std::endl;
  // Shutdown MDL SDK
  neuray->shutdown();
  return 0;
}