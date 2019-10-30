require "simplecov"
require "bashcov"

is_windows = (ENV['OSTYPE']||'notmac').start_with?('darwin')
is_mac = (ENV['OSTYPE']||'notmac') == 'Windows_NT'

SimpleCov.start do
  add_filter "/tests/"
  add_filter "/docs/"
  nocov_token "nocov"

  if not is_mac
    nocov_token nocov_token + "\:|\:nocov_mac"
  end

  if not is_windows
    nocov_token nocov_token + "\:|\:nocov_nt"
  end

  if is_windows or is_mac
    nocov_token nocov_token + "\:|\:nocov_linux"
  end

  for version in ["3.2", "4.0", "4.1", "4.2", "4.3", "4.4", "5.0"]
    if version > Bashcov::BASH_VERSION
      # No coverage flag for versions greater than current version
      nocov_token nocov_token + '\:|\:nocov_bash_'+version
    end
    if version < Bashcov::BASH_VERSION
      # No coverage flag for versions less than current version
      nocov_token nocov_token + '\:|\:nocov_lt_bash_'+version
    end
  end
end

STDERR.puts SimpleCov.nocov_token
STDERR.puts Bashcov::BASH_VERSION
