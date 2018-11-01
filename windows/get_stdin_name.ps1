
#*# windows/get_stdin_name.ps1

#**
# .. file:: get_stdin_name.ps1
#
# Gets the name of the stdin file/pipe on Windows. This only has a meaning in consoles like mintty like Git for Windows (mingw64), msys, cygwin, etc... On consoles like cmd.exe and powershell, they have no name, and the string "None" is returned
#
# ============ =========================================
# console      value
# ============ =========================================
# mingw64      \msys-????????????????-pty?-from-master
# piped mingw  \msys-????????????????-?????-pipe-0x??
# cygwin       \cygwin-????????????????-pty?-from-master
# piped cygwin \cygwin-????????????????-?????-pipe-0x??
# cmd          None
# powershell   None
# ============ =========================================
#**

# Not 100% sure if CharSet.Auto is 100% right here, but it works. May not work
# on a UTF-32 system. But you will at least get a "\" vs "None"
$script:memberDefinition =  @'

    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Auto)]
    public struct FILE_NAME_INFO
    {
        [MarshalAs(UnmanagedType.U4)]
        public UInt32 FileNameLength;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=1024)]
        public string FileName;
    }

    [DllImport("kernel32.dll", SetLastError=true)]
        public static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
        public static extern IntPtr GetStdHandle(
                [MarshalAs(UnmanagedType.U4)] Int32 nStdHandle);

    [DllImport("kernel32.dll", CharSet = CharSet.Ansi, SetLastError = true)]
        public static extern bool GetFileInformationByHandleEx(
                IntPtr hFile,
                int infoClass,
                out FILE_NAME_INFO fileInfo,
                uint dwBufferSize);

'@
#     [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
#         public static extern IntPtr CreateFile(
#                 [MarshalAs(UnmanagedType.LPTStr)] string filename,
#                 [MarshalAs(UnmanagedType.U4)] UInt32 access,
#                 [MarshalAs(UnmanagedType.U4)] UInt32 share,
#                 IntPtr securityAttributes, // optional SECURITY_ATTRIBUTES struct or IntPtr.Zero
#                 [MarshalAs(UnmanagedType.U4)] UInt32 creationDisposition,
#                 [MarshalAs(UnmanagedType.U4)] UInt32 flagsAndAttributes,
#                 IntPtr templateFile);

# '@

# $cp = [System.CodeDom.Compiler.CompilerParameters]::new()
# $cp.ReferencedAssemblies.AddRange(('System.Windows.Forms.dll', 'System.Drawing.dll'))
# $cp.CompilerOptions = '/unsafe'

Add-Type -MemberDefinition $script:memberDefinition -Name File -Namespace Kernel32 # -CompilerParameters $cp

# $VerbosePreference = "Continue"

try
{
    $fileHandle = [Kernel32.File]::GetStdHandle(-10)
    # $fileHandle = [Kernel32.File]::CreateFile("D:\src",
    #             [System.IO.FileAccess]::Read,
    #             [System.IO.FileShare]::ReadWrite,
    #             [System.IntPtr]::Zero,
    #             [System.IO.FileMode]::Open,
    #             [System.UInt32]0x02000000,
    #             [System.IntPtr]::Zero)

    if($fileHandle -eq -1)
    {
        throw "GetStdHandle: Error opening file -10"
    }

    # Output object
    $fileNameInfo = New-Object -TypeName Kernel32.File+FILE_NAME_INFO

    $bRetrieved = [Kernel32.File]::GetFileInformationByHandleEx($fileHandle,2,
        [ref]$fileNameInfo,
        [System.Runtime.InteropServices.Marshal]::SizeOf($fileNameInfo))

    if(!$bRetrieved)
    {
        Write-Output "None"
    }
    else
    {
        Write-Output $fileNameInfo.FileName
    }
}
catch
{
    throw $_
}
finally
{
    $bClosed = [Kernel32.File]::CloseHandle($fileHandle)

    if(!$bClosed)
    {
        Write-Warning "CloseHandle: Error closing handle $fileHandle of $Path"
    }
}
