export PATH=$(xcode-select -p)/usr/bin:$PATH
eval "$(/opt/homebrew/bin/brew shellenv)"

# Rust completions
. "$HOME/.cargo/env"

# OpenMP
export OpenMP_ROOT=$(/opt/homebrew/bin/brew --prefix)/opt/libomp
export CPPFLAGS="-I${OpenMP_ROOT}/include"
export LDFLAGS="$LDFLAGS -L${OpenMP_ROOT}/lib"

# SDL and other libs for easy linking
export LIBRARY_PATH="$LIBRARY_PATH:$(/opt/homebrew/bin/brew --prefix)/lib"

# local::lib
if [ -d ~/perl5 ]; then
    eval "$(perl -I$HOME/perl5/lib/perl5 -Mlocal::lib=$HOME/perl5)"
    export PATH="$HOME/perl5/bin:$PATH"
fi

# local git tree
if [ -d ~/git_tree ]; then
    export GIT_TREE="$HOME/git_tree"
elif [ -d /usr/local/git_tree ]; then
    export GIT_TREE="/usr/local/git_tree"
fi

if [ "$GIT_TREE" != "" ]; then
    export PATH="$PATH:$GIT_TREE/main/bin"
    export PERL5LIB="$PERL5LIB:$GIT_TREE/main/lib:$GIT_TREE/main/inc/Perl-Critic-Policy-BCritical/lib/"
fi

# local stuff
export PATH=/usr/local/bin:$PATH

# Perl modules etc
export PATH=/opt/homebrew/opt/perl/bin:$PATH

# My own utility scripts etc.
export PATH=$HOME/bin:$PATH

# Added by Toolbox App
export PATH="$PATH:/Users/fpierfederic/Library/Application Support/JetBrains/Toolbox/scripts"
