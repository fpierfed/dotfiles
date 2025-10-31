# local stuff
export PATH=/usr/local/bin:$PATH

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

# local::lib
if [ -d ~/perl5 ]; then
    eval "$(perl -I$HOME/perl5/lib/perl5 -Mlocal::lib=$HOME/perl5)"
    export PATH="$HOME/perl5/bin:$PATH"
fi

# Perl modules etc
export PATH=/opt/homebrew/opt/perl/bin:$PATH

# My own utility scripts etc.
export PATH=$HOME/bin:$PATH

# Proxy
# export HTTP_PROXY=http://webproxy:3128
# export HTTPS_PROXY=http://webproxy:3128
# export http_proxy=http://webproxy:3128
# export https_proxy=http://webproxy:3128
# export no_proxy=localhost,127.0.0.1,localaddress,.localdomain.com,.booking.com,booking.com,.okta.com,.gitlab.com

# Accomm Mods & Cancel
export SD_PROJECT=accommodation-reservation-modification
export SD_COMPONENT=modifications-api
if [ -d /Library/Java/JavaVirtualMachines/zulu-21.jdk/Contents/Home ]; then
    export JAVA_HOME=/Library/Java/JavaVirtualMachines/zulu-21.jdk/Contents/Home
fi

# Tokens etc.
if [ -f ~/.tokens ]; then
. ~/.tokens
fi
