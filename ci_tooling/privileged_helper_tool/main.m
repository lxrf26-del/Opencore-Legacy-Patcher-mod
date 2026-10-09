/*
    ------------------------------------------------
    OpenCore Legacy Patcher Privileged Helper Tool
    ------------------------------------------------
    Designed as an alternative to an XPC service,
    this tool is used to run commands as root.
    ------------------------------------------------
    Server and client must have the same signing
    certificate in order to run commands.
    ------------------------------------------------
*/

#import <Foundation/Foundation.h>
#import <Security/Security.h>
#include <libproc.h>

#define UTILITY_VERSION "1.0.0"

#define VALID_CLIENT_CERTIFICATE @"19FD838A17B096F42774B90A438950EC8052A4A5"

#define OCLP_PHT_ERROR_MISSING_ARGUMENTS           160
#define OCLP_PHT_ERROR_SET_UID_MISSING             161
#define OCLP_PHT_ERROR_SET_UID_FAILED              162
#define OCLP_PHT_ERROR_SELF_PATH_MISSING           163
#define OCLP_PHT_ERROR_PARENT_PATH_MISSING         164
#define OCLP_PHT_ERROR_SIGNING_INFORMATION_MISSING 165
#define OCLP_PHT_ERROR_INVALID_TEAM_ID             166
#define OCLP_PHT_ERROR_INVALID_CERTIFICATES        167
#define OCLP_PHT_ERROR_COMMAND_MISSING             168
#define OCLP_PHT_ERROR_COMMAND_FAILED              169
#define OCLP_PHT_ERROR_CATCH_ALL                   170


OSStatus checkModSignature(SecCodeRef code, NSString *identifier) {
    NSString *rule = [NSString stringWithFormat:@"certificate leaf = H\"%@\" and identifier \"%@\"", VALID_CLIENT_CERTIFICATE, identifier];
    SecRequirementRef requirement = NULL;
    OSStatus status = SecRequirementCreateWithString((__bridge CFStringRef)rule, kSecCSDefaultFlags, &requirement);
    if (status != errSecSuccess) {
        return status;
    }
    status = SecCodeCheckValidity(code, kSecCSDefaultFlags, requirement);
    if (status == errSecSuccess) {
        SecStaticCodeRef staticCode = NULL;
        status = SecCodeCopyStaticCode(code, kSecCSDefaultFlags, &staticCode);
        if (status == errSecSuccess) {
            status = SecStaticCodeCheckValidity(staticCode, kSecCSStrictValidate | kSecCSCheckNestedCode, requirement);
            CFRelease(staticCode);
        }
    }
    CFRelease(requirement);
    return status;
}

OSStatus checkModCaller(void) {
    SecCodeRef caller = NULL;
    NSDictionary *attributes = @{(__bridge NSString *)kSecGuestAttributePid: @(getppid())};
    OSStatus status = SecCodeCopyGuestWithAttributes(NULL, (__bridge CFDictionaryRef)attributes, kSecCSDefaultFlags, &caller);
    if (status != errSecSuccess) {
        return status;
    }
    status = checkModSignature(caller, @"com.dortania.opencore-legacy-patcher");
    CFRelease(caller);
    return status;
}

NSString *getProcessPath() {
    NSString *path = [[NSBundle mainBundle] executablePath];
    return path;
}

BOOL isSBitSet(NSString *path) {
    NSFileManager *fileManager = [NSFileManager defaultManager];
    NSDictionary *attributes = [fileManager attributesOfItemAtPath:path error:nil];
    if (attributes == nil) {
        return NO;
    }
    return (attributes.filePosixPermissions & S_ISUID) != 0;
}


int main(int argc, const char * argv[]) {
    @autoreleasepool {
        // We simply return if no arguments are passed
        if (argc < 2) {
            return OCLP_PHT_ERROR_MISSING_ARGUMENTS;
        }

        if (argc == 2 && (strcmp(argv[1], "--version") == 0 || strcmp(argv[1], "-v") == 0)) {
            printf("%s\n", UTILITY_VERSION);
            return 0;
        }

        // Verify whether we can run as root
        NSString *processPath = getProcessPath();
        if (processPath == nil) {
            return OCLP_PHT_ERROR_SELF_PATH_MISSING;
        }

        if (!isSBitSet(processPath)) {
            return OCLP_PHT_ERROR_SET_UID_MISSING;
        }

        setuid(0);
        if (getuid() != 0) {
            return OCLP_PHT_ERROR_SET_UID_FAILED;
        }

        SecCodeRef selfCode = NULL;
        OSStatus signatureStatus = SecCodeCopySelf(kSecCSDefaultFlags, &selfCode);
        if (signatureStatus != errSecSuccess) {
            return OCLP_PHT_ERROR_SIGNING_INFORMATION_MISSING;
        }
        signatureStatus = checkModSignature(selfCode, @"com.dortania.opencore-legacy-patcher.privileged-helper");
        CFRelease(selfCode);
        if (signatureStatus != errSecSuccess || checkModCaller() != errSecSuccess) {
            return OCLP_PHT_ERROR_INVALID_CERTIFICATES;
        }

        NSString *command = nil;
        NSArray *arguments = @[];
        if (argc == 2) {
            command = [NSString stringWithUTF8String:argv[1]];
        } else {
            command = [NSString stringWithUTF8String:argv[1]];
            for (int i = 2; i < argc; i++) {
                arguments = [arguments arrayByAddingObject:[NSString stringWithUTF8String:argv[i]]];
            }
        }

        // Verify command exists
        if (![[NSFileManager defaultManager] fileExistsAtPath:command]) {
            return OCLP_PHT_ERROR_COMMAND_MISSING;
        }

        NSTask *task = [[NSTask alloc] init];
        [task setLaunchPath:command];
        [task setArguments:arguments];
        [task launch];
        [task waitUntilExit];
        return [task terminationStatus];
    }
    return OCLP_PHT_ERROR_CATCH_ALL; // Should never reach here
}