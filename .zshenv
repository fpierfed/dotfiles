. "$HOME/.cargo/env"

# SDL and other libs for easy linking
export LIBRARY_PATH="$LIBRARY_PATH:$(/opt/homebrew/bin/brew --prefix)/lib"

# OpenMP
export LDFLAGS="-L/opt/homebrew/opt/libomp/lib"
export CPPFLAGS="-I/opt/homebrew/opt/libomp/include"
