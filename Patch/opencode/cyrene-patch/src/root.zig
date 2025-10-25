const std = @import("std");
const zz = @import("zigzag");
const util = @import("util.zig");

const windows = std.os.windows;
const unicode = std.unicode;

const DLL_PROCESS_ATTACH = 1;

extern "kernel32" fn AllocConsole() callconv(.winapi) void;
extern "kernel32" fn FreeConsole() callconv(.winapi) void;

const ntdll_name = unicode.utf8ToUtf16LeStringLiteral("ntdll.dll");
const wintrust_dll_name = std.unicode.utf8ToUtf16LeStringLiteral("wintrust.dll");
const game_assembly_name = unicode.utf8ToUtf16LeStringLiteral("GameAssembly.dll");

const wintrust_funcs: []const [:0]const u8 = &.{
    "CryptCATAdminEnumCatalogFromHash",
    "CryptCATCatalogInfoFromContext",
    "CryptCATAdminReleaseCatalogContext",
};

const wintrust_stub: []const u8 = &.{ 0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3 };

pub var base: usize = undefined;

fn onAttach() void {
    FreeConsole();
    AllocConsole();

    std.fs.File.stdout().writeAll(
        \\             .@@:::                       #                 
        \\            @::@@-%:@       @@@@@@@@    %  @                
        \\            .-= #--@::* @#:::::::::@@@@@    @               
        \\            @=.  =:-:@@@:::::::-#----=@@    .=              
        \\           @:#.-:-@:%.-@@::::---@:----@-@   .:@    @        
        \\            . -*@@::@---------:---@:--@   @::::-@ @#        
        \\         @-@:++=+*@#--:+@------@----@:-.   ::@:-  @@@       
        \\       @@:+@@=@@-@--------------@----@:-@. :::@-@%@@  @     
        \\      @:::-*:@--@-----:-::---::------@::::----@-+-@         
        \\     @::-----:@-----::::::-:-::-:-:---@:::-::::@----@%      
        \\    @::----::@-------:::-:---:--:-:---@:::---::#------@     
        \\   @:------::*----@---------------@=--@:%:-----:@------     
        \\  @-:-----::@----@-::--------------@--@:-#-------@%----@    
        \\  @----+:::@----+@:::---------------@-@:-@:-------::%@@@    
        \\ @----@:-::@--@@@#:::--------------#..@::@::---------@-@    
        \\ @--@@:--::@--@@@=@@::---------@---@..@-@--:---@@+*@@--#    
        \\ @-@@:---::@@@@   ###@@-------@@@@@@@@@@-@#:------@%..@%    
        \\ *@ @:---@@:::++++==##@@.@@@@@=.@@@@@@#.@*:::-----@..-@@    
        \\ #@@::-@::::::+=======@.........@   ###@.@:::------@@--@    
        \\ @ @::%::::::::@...=+@..........+++=+###@@:::----@-----@    
        \\   :::@::::::::::...............+=======@::------@----@@    
        \\  @:::-@:::::::::....@..@........=...==@:::------@---@=*    
        \\   *::--@:::::::.....-@@.@@.....:::@@::@::-------@--@====@  
        \\   @:::---@::::.................::::::@::-----@--@@====++++@
        \\  @-@-=:-----@@@................:::::@:--@----@--+===+++**@ 
        \\ @====@::--@@--@    @@@@@@+.....:#@@%---@@----@---@@ @@@@   
        \\ @@@@@+@:---@                            *---@+@@%++@       
        \\    @=++@@@@@@                          @---@ @@+++@@       
        \\                                     @@-@@@                 
        \\
    ) catch {};

    std.log.debug("Successfully injected. Waiting for the game startup.", .{});
    std.log.debug("To work with Cyrene-SR: https://git.xeondev.com/cyrene-sr/cyrene-sr", .{});

    if (isWine()) {
        const wintrust = windows.kernel32.LoadLibraryW(wintrust_dll_name).?;
        inline for (wintrust_funcs) |func_name| {
            const func: [*]u8 = @ptrCast(windows.kernel32.GetProcAddress(wintrust, func_name).?);
            var prot: windows.DWORD = windows.PAGE_EXECUTE_READWRITE;
            windows.VirtualProtect(@ptrCast(func), 6, prot, &prot) catch unreachable;
            @memcpy(func, wintrust_stub);
            windows.VirtualProtect(@ptrCast(func), 6, prot, &prot) catch unreachable;
        }
    }

    base = while (true) {
        if (windows.kernel32.GetModuleHandleW(game_assembly_name)) |addr| break @intFromPtr(addr);
        std.Thread.sleep(std.time.ns_per_ms * 100);
    };

    std.log.debug("GameAssembly is located at: 0x{X}", .{base});
    std.Thread.sleep(std.time.ns_per_s * 2);

    disableMemoryProtection() catch |err| {
        std.log.err("Failed to disable memory protection: {}", .{err});
        return;
    };

    var pca = zz.PageChunkAllocator.init() catch unreachable;
    const allocator = pca.allocator();

    _ = intercept(allocator, base + 0x156E8390, MakeInitialUrlHook);

    @as(*usize, @ptrFromInt(base + 0x5D33CE0)).* = util.il2cppStringNew(@embedFile("sdk_public_key.xml"));

    const dither_func: usize = 0x74264B0;
    const hoyopass_init: usize = 0x12EC2090;

    var prot: windows.DWORD = windows.PAGE_EXECUTE_READWRITE;
    windows.VirtualProtect(@ptrFromInt(base + dither_func), 1, prot, &prot) catch unreachable;
    @as(*u8, @ptrFromInt(base + dither_func)).* = 0xC3;
    windows.VirtualProtect(@ptrFromInt(base + dither_func), 1, prot, &prot) catch unreachable;

    prot = windows.PAGE_EXECUTE_READWRITE;
    windows.VirtualProtect(@ptrFromInt(base + hoyopass_init), 1, prot, &prot) catch unreachable;
    @as(*u8, @ptrFromInt(base + hoyopass_init)).* = 0xC3;
    windows.VirtualProtect(@ptrFromInt(base + hoyopass_init), 1, prot, &prot) catch unreachable;

    std.log.debug("Successfully initialized", .{});
}

const MakeInitialUrlHook = struct {
    const global_dispatch_prefix = unicode.utf8ToUtf16LeStringLiteral("https://globaldp-beta-cn01.bhsr.com");
    const cn_sdk_domain = unicode.utf8ToUtf16LeStringLiteral("mihoyo.com");
    const global_sdk_domain = unicode.utf8ToUtf16LeStringLiteral("hoyoverse.com");

    const custom_dispatch_prefix = unicode.utf8ToUtf16LeStringLiteral("http://127.0.0.1:10100");
    const custom_sdk_prefix = unicode.utf8ToUtf16LeStringLiteral("http://127.0.0.1:20100");

    pub var originalFn: *const fn (usize, usize) callconv(.c) usize = undefined;

    pub fn callback(a1: usize, a2: usize) callconv(.c) usize {
        var buf: [4096]u8 = undefined;

        const str = util.readCSharpString(a1);
        const len = std.unicode.utf16LeToUtf8(&buf, str) catch unreachable;
        std.log.debug("{s}", .{buf[0..len]});

        if (std.mem.startsWith(u16, str, global_dispatch_prefix)) {
            std.log.debug("dispatch request detected.", .{});
            util.csharpStringReplace(a1, global_dispatch_prefix, custom_dispatch_prefix);
        } else if (std.mem.indexOf(u16, str, cn_sdk_domain)) |index| {
            std.log.debug("CN SDK request detected.", .{});
            util.csharpStringReplace(a1, str[0 .. index + cn_sdk_domain.len], custom_sdk_prefix);
        } else if (std.mem.indexOf(u16, str, global_sdk_domain)) |index| {
            std.log.debug("GLOBAL SDK request detected.", .{});
            util.csharpStringReplace(a1, str[0 .. index + global_sdk_domain.len], custom_sdk_prefix);
        }

        return @This().originalFn(a1, a2);
    }
};

pub fn intercept(ca: zz.ChunkAllocator, address: usize, hook_struct: anytype) zz.Hook(@TypeOf(hook_struct.callback)) {
    const hook = zz.Hook(@TypeOf(hook_struct.callback)).init(ca, @ptrFromInt(address), hook_struct.callback) catch |err| {
        std.log.err("failed to intercept function at 0x{X}: {}", .{ address - base, err });
        @panic("intercept failed");
    };

    hook_struct.originalFn = hook.delegate;
    return hook;
}

pub export fn DllMain(_: windows.HINSTANCE, reason: windows.DWORD, _: windows.LPVOID) callconv(.winapi) windows.BOOL {
    if (reason == DLL_PROCESS_ATTACH) {
        const thread = std.Thread.spawn(.{}, onAttach, .{}) catch unreachable;
        thread.detach();
    }

    return 1;
}

fn disableMemoryProtection() !void {
    const ntdll = windows.kernel32.GetModuleHandleW(ntdll_name).?;
    const proc_addr = windows.kernel32.GetProcAddress(ntdll, "NtProtectVirtualMemory").?;

    const nt_func = nt_func: {
        if (isWine()) {
            break :nt_func windows.kernel32.GetProcAddress(ntdll, "NtPulseEvent").?;
        } else {
            break :nt_func windows.kernel32.GetProcAddress(ntdll, "NtQuerySection").?;
        }
    };

    var protection: windows.DWORD = windows.PAGE_EXECUTE_READWRITE;
    try windows.VirtualProtect(proc_addr, 1, protection, &protection);

    const routine: *u32 = @ptrCast(@alignCast(nt_func));
    const routine_val = @as(*usize, @ptrCast(@alignCast(routine))).*;
    const lower_bits_mask = ~(@as(u64, 0xFF) << 32);
    const lower_bits = routine_val & @as(usize, @intCast(lower_bits_mask));

    const offset_val = @as(*const u32, @ptrFromInt(@as(usize, @intFromPtr(routine)) + 4)).*;
    const upper_bits = @as(usize, @intCast(@subWithOverflow(offset_val, 1).@"0")) << 32;
    const result = lower_bits | upper_bits;
    @as(*usize, @ptrCast(@alignCast(proc_addr))).* = result;

    try windows.VirtualProtect(proc_addr, 1, protection, &protection);
}

fn isWine() bool {
    const ntdll = windows.kernel32.GetModuleHandleW(ntdll_name).?;
    return windows.kernel32.GetProcAddress(ntdll, "wine_get_version") != null;
}
