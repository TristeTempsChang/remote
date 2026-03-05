# Charger les alias si le fichier existe
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# Prompt simple
PS1="\u@\h:\w$ "
