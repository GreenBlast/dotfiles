"   __     ___              ____             __ _
"   \ \   / (_)_ __ ___    / ___|___  _ __  / _(_) __ _
"    \ \ / /| | '_ ` _ \  | |   / _ \| '_ \| |_| |/ _` |
"     \ V / | | | | | | | | |__| (_) | | | |  _| | (_| |
"      \_/  |_|_| |_| |_|  \____\___/|_| |_|_| |_|\__, |
"                                                 |___/
"
" Place of this configuration file:
"   ~/.config/nvim/init.vim


" ====================================================================
" General settings
" ====================================================================

" Create the required directories
" {{{
    silent !mkdir ~/nvim.local > /dev/null 2>&1
    silent !mkdir ~/nvim.local/tmp > /dev/null 2>&1
    silent !mkdir ~/nvim.local/undo > /dev/null 2>&1
" }}}

" Set up leaders:
" <Leader>
let mapleader = ","
" <LocalLeader>
let maplocalleader = "\\"

" Setting python hosts location, this is needed for some of the plugins
" Mainly Shougos plugins (deoplete, denite)
let g:python_host_prog = '/usr/bin/python2'
let g:python3_host_prog = '/usr/bin/python3'

" Always show status bar
set laststatus=2

" Let plugins show effects after 500ms, not 4s
set updatetime=500

" Hybrid numbering
set relativenumber showmatch
set number

" Not compatible with vi, does nothing on Nvim
set nocompatible
filetype plugin indent on

" Indenting the next lines in a scope by 4 spaces
set shiftwidth=4

" Tabs are expanded to spaces
set expandtab

" Backspace can do: (Delete full indents, delete over newline, and delete over
" the start point of the insert mode), In new vims this is usually the default
" 2 means all this things in older versions
set backspace=indent,eol,start

" Tab is 4 spaces
set tabstop=4

" Highlight search"
set hlsearch

" Case insensitive search
set ignorecase

" Escape modes faster
set timeoutlen=1000 ttimeoutlen=0

" Setting special chars"
set list
set listchars=tab:→\ ,trail:·,extends:>,precedes:<

" Setting fold columns (Add markings to the numbers bar for open folds)
set foldcolumn=3

" VimTip 20: Are *.swp and *~ files littering your working directory?
" {{{
    set backup
    set backupext=~
    set backupdir=~/nvim.local/tmp
    set directory=~/nvim.local/tmp

    " let's add undo
    set undofile
    set undodir=~/nvim.local/undo
" }}}

" Automatically change window's cwd to file's dir
set autochdir


" Setting vim to load local vimrc files
set exrc
set secure

" Switch spell check on/off (grammar check)
setlocal spell spelllang=en_us      "let's use English by default
set nospell                         "by default spell is off

" Enable syntax
if !exists("g:syntax_on")
    syntax enable
endif

" Allow backspacing over everything in insert mode
set backspace=indent,eol,start

" If vim versioning is active, don't save backup, use versions instead
if has("vms")
    " do not keep a backup file, use versions instead
    set nobackup
else
    " keep a backup file (restore to previous version)
    set backup
    " keep an undo file (undo changes after closing)
    set undofile
endif

" keep 50 lines of command line history
set history=50

" show the cursor position all the time
set ruler

" display incomplete commands
set showcmd

" do incremental searching
set incsearch

" Draw only what needed, helps scroll performance
set lazyredraw

" Setting the maximum culomns to parse syntax, also helps with scroll performance
set synmaxcol=128

" Minimum sync lines element to search for syntax parsing, aslo helps with scroll performance
syntax sync minlines=256

" In many terminal emulators the mouse works just fine
if has('mouse')
    set mouse=a
endif

" Setting copy to system clipboard
" set clipboard=unnamed
" Disabling clipboard for faster load times
set clipboard=""

" netrw settings
" {{{
    " Setting netrw to tree style
    let g:netrw_liststyle = 3

    "Remove the banner
    " let g:netrw_banner = 0

    " Open in a new split
    " let g:netrw_browse_split = 1

    " Set split to 25% of page
    " let g:netrw_winsize = 25
" }}}

" Autoinstall vim-plug
" {{{
    " https://github.com/junegunn/vim-plug
    let s:vim_plug_dir=expand($HOME.'/.config/nvim/autoload')
    if !filereadable(s:vim_plug_dir.'/plug.vim')
        execute '!wget https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim -P '.s:vim_plug_dir
        let s:install_plug=1
    endif
" }}}

" ====================================================================
" Plugins start
" ====================================================================

" This is the start of the plugins section
call plug#begin('~/nvim.local/plugged')

" ====================================================================
" Color schemes
" ====================================================================

Plug 'michalbachowski/vim-wombat256mod'
Plug 'joshdick/onedark.vim'
Plug 'https://github.com/ninja/sky'
Plug 'freeo/vim-kalisi'

" ====================================================================
" Visuals
" ====================================================================

" Indenting lines with given characters
Plug 'Yggdroot/indentLine'
" {{{
    " :h indentLine.txt
    let g:indentLine_char = '¦'
    "
    " let g:indentLine_char = '┆'
    "
    " let g:indentLine_char = '┊'
    "
    " let g:indentLine_char = '│'
    " disable it
    let g:indentLine_enabled = 1

    " The indentlines will not show up in the cursorline:
    let g:indentLine_concealcursor = ''
" }}}

" Json support
Plug 'elzr/vim-json'
" {{{
    " indentLine conceals quotes in json files; this puts them back:
    let g:vim_json_syntax_conceal = 0
" }}}


" ====================================================================
" Completion
" ====================================================================

" Complete code snippets
Plug 'SirVer/ultisnips'
" {{{
    " Trigger configuration. Do not use <tab> if you use it for completion
    " let g:UltiSnipsExpandTrigger="<tab>"
    let g:UltiSnipsExpandTrigger="<C-j>"
    let g:UltiSnipsJumpForwardTrigger="<tab>"
    let g:UltiSnipsJumpBackwardTrigger="<s-tab>"

    " If you want :UltiSnipsEdit to split your window.
    let g:UltiSnipsEditSplit="vertical"
" }}}

" Ready made snippets for ultisnips and snipmate
Plug 'honza/vim-snippets'
" {{{
" }}}

" Dark powered async autocomplete
Plug 'Shougo/deoplete.nvim'
" {{{
    let g:deoplete#enable_at_startup = 1
    if !exists('g:deoplete#omni#input_patterns')
      let g:deoplete#omni#input_patterns = {}
    endif
    " let g:deoplete#disable_auto_complete = 1

    " Close on finish completion or exiting insert
    autocmd InsertLeave,CompleteDone * if pumvisible() == 0 | pclose | endif

    " Deoplete tab-complete
    inoremap <expr><tab> pumvisible() ? "\<c-n>" : "\<tab>"
    inoremap <expr><S-Tab> pumvisible() ? "\<c-p>" : "\<tab>"

    " Omnifuncs
    augroup omnifuncs
      autocmd!
      autocmd FileType css setlocal omnifunc=csscomplete#CompleteCSS
      autocmd FileType html,markdown setlocal omnifunc=htmlcomplete#CompleteTags
      autocmd FileType javascript setlocal omnifunc=javascriptcomplete#CompleteJS
      autocmd FileType python setlocal omnifunc=pythoncomplete#Complete
      autocmd FileType xml setlocal omnifunc=xmlcomplete#CompleteTags
    augroup end
" }}}

" Adding autocomplete support for python
Plug 'zchee/deoplete-jedi'
" {{{
" }}}

" Auto complete support for c based languages
Plug 'zchee/deoplete-clang'
" {{{
    " Settings for deoplete clang - Location is different for each machine
    if !empty(glob('/usr/lib/x86_64-linux-gnu/libclang-3.5.so.1')) && !empty(glob('/usr/lib/llvm-3.8/lib/clang'))
        let g:deoplete#sources#clang#libclang_path = '/usr/lib/x86_64-linux-gnu/libclang-3.5.so.1'
        let g:deoplete#sources#clang#clang_header = '/usr/lib/llvm-3.8/lib/clang'
    elseif !empty(glob('/usr/lib/x86_64-linux-gnu/libclang-3.5.so.1')) && !empty(glob('/usr/lib/llvm-3.5/lib/clang'))
        let g:deoplete#sources#clang#libclang_path = '/usr/lib/x86_64-linux-gnu/libclang-3.5.so.1'
        let g:deoplete#sources#clang#clang_header = '/usr/lib/llvm-3.5/lib/clang'
    endif
" }}}


" Add ability to surround given strings with characters
Plug 'tpope/vim-surround'
" {{{
" }}}

" Add dot repeat function to tpope plugins
Plug 'tpope/vim-repeat'
" {{{
    " Some intuitive surrounding (Surround with ",' or `)
    nnoremap <silent> <Plug>SurroundWordWithApostrophe  viw<esc>a'<esc>hbi'<esc>lel
        \ :call repeat#set("\<Plug>SurroundWordWithApostrophe", v:count)<cr>
    nmap <Leader>'  <Plug>SurroundWordWithApostrophe

    nnoremap <silent> <Plug>SurroundWordWithQuote  viw<esc>a"<esc>hbi"<esc>lel
        \ :call repeat#set("\<Plug>SurroundWordWithQuote", v:count)<cr>
    nmap <Leader>"  <Plug>SurroundWordWithQuote

    nnoremap <silent> <Plug>SurroundWordWithBacktick  viw<esc>a`<esc>hbi`<esc>lel
        \ :call repeat#set("\<Plug>SurroundWordWithBacktick", v:count)<cr>
    nmap <Leader>`  <Plug>SurroundWordWithBacktick

    vnoremap <Leader>'  <esc>`<i'<esc>`>la'<esc>
    vnoremap <Leader>"  <esc>`<i"<esc>`>la"<esc>
    vnoremap <Leader>`  <esc>`<i`<esc>`>la`<esc>
" }}}

" Enhance surround, add closing completion for tags(HTML, XML, etx...)
Plug 'tpope/vim-ragtag'
" {{{
" }}}

" Automatic closing of quotes, parenthesis, brackets, etc.
Plug 'Raimondi/delimitMate'
" {{{
" }}}

" ====================================================================
" Git
" ====================================================================

" Adds various git functionality to vim
Plug 'tpope/vim-fugitive'
" {{{
  nnoremap <leader>gs :Gstatus<CR>
  nnoremap <leader>gc :Gcommit -v -q<CR>
  nnoremap <leader>ga :Gcommit --amend<CR>
  nnoremap <leader>gt :Gcommit -v -q %<CR>
  nnoremap <leader>gd :Gdiff<CR>
  nnoremap <leader>ge :Gedit<CR>
  nnoremap <leader>gr :Gread<CR>
  nnoremap <leader>gw :Gwrite<CR><CR>
  nnoremap <leader>gl :silent! Glog<CR>
  nnoremap <leader>gp :Ggrep<Space>
  nnoremap <leader>gm :Gmove<Space>
  nnoremap <leader>gb :Git branch<Space>
  nnoremap <leader>go :Git checkout<Space>
  nnoremap <leader>gps :Dispatch! git push<CR>
  nnoremap <leader>gpl :Dispatch! git pull<CR>
" }}}

" Adds gutter git annotations
Plug 'airblade/vim-gitgutter'
" {{{
    " Let vim-gitgutter do its thing on large files
    let g:gitgutter_max_signs=10000
" }}}

" ====================================================================
" Syntax
" ====================================================================

" Highlight python
autocmd BufRead,BufNewFile *.py let python_highlight_all=1

" Neomake is async builder for neovim
Plug 'neomake/neomake'
" {{{
    " run neomake on the current file on every write:
    autocmd! BufWritePost * Neomake
    let g:neomake_python_enabled_makers = ['pylint']
    let g:neomake_python_pylint_maker = {
        \ 'args': [
            \ '--output-format=text',
            \ '--msg-template="{path}:{line}:{column}:{C}: ({msg_id})[{symbol}] {msg}"',
            \ '--reports=no'
        \ ],
        \ 'errorformat':
            \ '%A%f:%l:%c:%t: %m,' .
            \ '%A%f:%l: %m,' .
            \ '%A%f:(%l): %m,' .
            \ '%-Z%p^%.%#,' .
            \ '%-G%.%#',
        \ 'postprocess': [
        \   function('neomake#postprocess#GenericLengthPostprocess'),
        \   function('neomake#makers#ft#python#PylintEntryProcess'),
        \ ]}
" }}}


" Unimpaired adds various shortcuts
Plug 'tpope/vim-unimpaired'
" {{{
" }}}

" Comment stuff out
Plug 'tpope/vim-commentary'
" {{{
" }}}

" Adds markdown support
Plug 'tpope/vim-markdown', { 'for': 'markdown' }
" {{{
" }}}

" ====================================================================
" Session management
" ====================================================================

" Manages vim session save and restore in response to certain events
Plug 'tpope/vim-obsession'
" {{{
" }}}

" ====================================================================
" Appearance
" ====================================================================

" Plug 'bling/vim-airline'
Plug 'vim-airline/vim-airline'
" {{{
    " if fonts are not installed, add a workaround
    if empty($FONTS_INSTALLED)
        let g:airline_powerline_fonts = 1

        if !exists('g:airline_symbols')
            let g:airline_symbols = {}
        endif

        " old vim-powerline symbols
        let g:airline_left_sep = '⮀'
        let g:airline_left_alt_sep = '⮁'
        let g:airline_right_sep = '⮂'
        let g:airline_right_alt_sep = '⮃'
        let g:airline_symbols.branch = '⭠'
        let g:airline_symbols.readonly = '⭤'
        let g:airline_symbols.linenr = '⭡'

        " Unicode symbols
        let g:airline_left_sep = '»'
        let g:airline_left_sep = '▶'
        let g:airline_right_sep = '«'
        let g:airline_right_sep = '◀'
        let g:airline_symbols.linenr = '¶'
        let g:airline_symbols.paste = 'ρ'
        let g:airline_symbols.paste = 'Þ'
        let g:airline_symbols.paste = '∥'
        let g:airline_symbols.whitespace = 'Ξ'
    endif
" }}}

" Themes for vim airline
Plug 'vim-airline/vim-airline-themes'
" {{{
    " also install the system package 'powerline-fonts'
    let g:airline_powerline_fonts = 1
    " Enable the list of buffers
    let g:airline#extensions#tabline#enabled = 1
    " Show just the filename
    let g:airline#extensions#tabline#fnamemod = ':t'

    let g:airline#extensions#tabline#left_sep = ''
    let g:airline#extensions#tabline#left_alt_sep = '|'
" }}}

" ====================================================================
" Buffers
" ====================================================================

" Adds BufOnly command to close all other buffers
Plug 'vim-scripts/BufOnly.vim'
" {{{
" }}}

" ====================================================================
" Navigation
" ====================================================================.

" Vim HardTime make it hard to use vim anti-patterns (Like using j to go down
" lines)
Plug 'takac/vim-hardtime'
" {{{
    let g:hardtime_default_on = 1
    let g:hardtime_showmsg = 1
" }}}

" Easymotion let you get fast to locations in buffer
Plug 'easymotion/vim-easymotion'
" {{{

    " Setting an easymotion search
    map <Space>s <Plug>(easymotion-sn)
    omap <Space>s <Plug>(easymotion-tn)
" }}}

" Additions to easymotion
Plug 'haya14busa/incsearch.vim'
Plug 'haya14busa/incsearch-fuzzy.vim'
Plug 'haya14busa/incsearch-easymotion.vim'

function! s:config_easyfuzzymotion(...) abort
  return extend(copy({
  \   'converters': [incsearch#config#fuzzy#converter()],
  \   'modules': [incsearch#config#easymotion#module()],
  \   'keymap': {"\<CR>": '<Over>(easymotion)'},
  \   'is_expr': 0,
  \   'is_stay': 1
  \ }), get(a:, 1, {}))
endfunction

let g:incsearch#auto_nohlsearch = 1
noremap <silent><expr> s incsearch#go(<SID>config_easyfuzzymotion())

" Fzf is a fuzzy searcher that uses ag - The Silver Searcher
Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
" {{{

    " [Tags] Command to generate tags file
    let g:fzf_tags_command = 'ctags -R'


    " Helpful completions while in insert mode
    imap <c-x><c-k> <plug>(fzf-complete-word)
    imap <c-x><c-f> <plug>(fzf-complete-path)
    imap <c-x><c-j> <plug>(fzf-complete-file-ag)
    imap <c-x><c-l> <plug>(fzf-complete-line)

    " Mixes the finds of FZF with the recent files in vim
    command! FZFMix call fzf#run({
            \'source':  'bash -c "'.
            \               'echo -e \"'.join(v:oldfiles, '\n').'\";'.
            \               'ag -l -g \"\"'.
            \           '"',
            \'sink' : 'e ',
            \'dir' : './/',
            \'options' : '-e -m --reverse',
            \'window' : 'enew',
            \})

    " Adding functionality to get root if in git repo, and FZF on it
    function! s:find_git_root()
        return system('git rev-parse --show-toplevel 2> /dev/null')[:-2]
    endfunction
    command! ProjectFiles execute 'Files' s:find_git_root()

    " FZF keymaps
    " Git files or current directory
    nnoremap <Leader>kk :ProjectFiles<CR>

    " Recent files
    nnoremap <Leader>kr :FZFMru<CR>

    " Open buffers
    nnoremap <Leader>kb :Buffers<CR>

    " Lines in buffer
    nnoremap <Leader>kl :BLines<CR>

    " Git status files
    nnoremap <Leader>kg :GFiles?<CR>

    " Tags in buffer
    nnoremap <Leader>kt :BTags<CR>

    " Key mappings
    nnoremap <Leader>km :Maps<CR>

    " Ag pattern
    nnoremap <Leader>ka :Ag<CR>

    command! -nargs=+ -complete=file -bar FZFLocation FZF <args>

    " FZF pattern
    nnoremap <Leader>kf :FZFLocation<space>

" }}}

" Most Recent Used for fzf
Plug 'lvht/fzf-mru'
" {{{
    " set max lenght for the mru file list
    let g:fzf_mru_file_list_size = 100 " default value
    " set path pattens that should be ignored
    let g:fzf_mru_ignore_patterns = 'fugitive\|\.git/\|\_^/tmp/' " default value
" }}}

" Augmenting vim's builtin netrw
Plug 'tpope/vim-vinegar'
" {{{
" }}}

" ====================================================================
" Tags
" ====================================================================

" Adds an IDE like viewer for tags (Needs ctags installed)
Plug 'majutsushi/tagbar'
" {{{
    nnoremap <F4> :TagbarToggle<cr>
" }}}

" ====================================================================
" VimWiki
" ====================================================================

" A wiki system for vim for knowledge management
Plug 'vimwiki/vimwiki'
" {{{
" }}}

" ====================================================================
" Plugins end
" ====================================================================

" Ending of plugins section
call plug#end()

" Setting the color scheme needs to be after plug end
" {{{
    set background=dark
    colorscheme kalisi
    " black background:
    hi Normal  ctermbg=None guifg=None guibg=None gui=none
    " black background at the end of file too (with lines ~):
    hi NonText ctermbg=None guifg=None guibg=None gui=none
" }}}

" ====================================================================
" Functions, Keymaps, Autocommands
" ====================================================================

" Convenient command to see the difference between the current buffer and the
" file it was loaded from, thus the changes you made.
" Only define it when not defined already.
if !exists(":DiffOrig")
    command! DiffOrig let g:diffline = line('.') | vert new | set bt=nofile | r ++edit # | 0d_ | diffthis | :exe "norm! ".g:diffline."G" | wincmd p | diffthis | wincmd p
endif

nnoremap <Leader>do :DiffOrig<cr>
nnoremap <leader>dc :q<cr>:diffoff<cr>:exe "norm! ".g:diffline."G"<cr>

" Don't use Ex mode, use Q for formatting
map Q gq

" CTRL-U in insert mode deletes a lot.  Use CTRL-G u to first break undo,
" so that you can undo CTRL-U after inserting a line break.
inoremap <C-U> <C-G>u<C-U>

" Allow saving of files as sudo when I forgot to start vim using sudo."
cmap w!! w !sudo tee > /dev/null %

" XML Lint
map @@x !%xmllint --format --recover -^M

" Map up/down arrow keys to unimpaired commands
nmap <Up> [e
nmap <Down> ]e
vmap <Up> [egv
vmap <Down> ]egv

" Map left/right arrow keys to indendation
nmap <Left> <<
nmap <Right> >>
vmap <Left> <gv
vmap <Right> >gv

" Un-highlighting search with \/
noremap <Leader>/ :nohls<CR>

" Exiting insert mode with jk
inoremap jk <Esc><Esc>

" Hard mode - Setting escape not to work in insert mode,
inoremap <esc> <nop>
inoremap <Left> <nop>
inoremap <Right> <nop>
inoremap <Up> <nop>
inoremap <Down> <nop>

" Search and replace current hightlighted visual
vnoremap <C-r> "hy:%s/<C-r>h//gc<left><left><left>

" Make it easy to update/reload .vimrc
" {{{
    "src: source rc file
    "erc: edit rc file
    nnoremap <Leader>src :source $MYVIMRC<cr>
    nnoremap <Leader>erc :e $MYVIMRC<cr>
    " nnoremap <Leader>erc :vsplit $MYVIMRC<cr>
" }}}

" Counting all occurances under cursor
map ,* *<C-O>:%s///gn<CR>

" Vim -b : edit binary using xxd-format!
augroup Binary
    au!
    au BufReadPre  *.bin let &bin=1
    au BufReadPost *.bin if &bin | %!xxd
    au BufReadPost *.bin set ft=xxd | endif
    au BufWritePre *.bin if &bin | %!xxd -r
    au BufWritePre *.bin endif
    au BufWritePost *.bin if &bin | %!xxd
    au BufWritePost *.bin set nomod | endif
augroup END

" Remove trailing whitespaces, strip, trim
" {{{
    autocmd BufWritePre *.txt :%s/\s\+$//e
    autocmd BufWritePre *.py :%s/\s\+$//e
    autocmd BufWritePre *.scala :%s/\s\+$//e
    autocmd BufWritePre *.pl :%s/\s\+$//e
    autocmd BufWritePre *.php :%s/\s\+$//e
    autocmd BufWritePre *.java :%s/\s\+$//e
    autocmd BufWritePre *.md :%s/\s\+$//e
    autocmd BufWritePre *.h :%s/\s\+$//e
    autocmd BufWritePre *.cpp :%s/\s\+$//e
    autocmd BufWritePre *.tex :%s/\s\+$//e
    autocmd BufWritePre *.vim :%s/\s\+$//e
    autocmd BufWritePre *.nfo :%s/\s\+$//e
    autocmd BufWritePre *.json :%s/\s\+$//e
    autocmd BufWritePre *.rs :%s/\s\+$//e
    autocmd BufWritePre *.config :%s/\s\+$//e
    autocmd BufWritePre *.wiki :%s/\s\+$//e
" }}}

" This block sets tmux activity to off, since for some reason NeoVim causes an
" activity when leaving the pane
if exists('$TMUX')
    augroup tmux_no_activity
        autocmd!
        autocmd VimEnter * silent! !tmux set-window-option monitor-activity off > /dev/null 2>&1
        autocmd VimLeave * silent! !tmux set-window-option monitor-activity on
    augroup end
endif

" Setting clipboard
  nnoremap <leader>c :set clipboard=unnamed<CR>
