"                                _
"                               (_)
"          _ __   ___  _____   ___ _ __ ___
"         | '_ \ / _ \/ _ \ \ / / | '_ ` _ \
"         | | | |  __/ (_) \ V /| | | | | | |
"         |_| |_|\___|\___/ \_/ |_|_| |_| |_|
"
"
" NeoVim config file adapted from Jabba Laci
"
" Place of this configuration file:
"   ~/.config/nvim/init.vim
"
" F1:    NERDTreeToggleAndFind() [show current file]
" F2:    NERDTreeToggle()
" F3:    Unite file_mru
" F4:    toggle tagbar
" F5:    :Autoformat
" F6:    toggle wrap
" F7:    toggle number
" F8:    close empty buffers
" F9:    run with Python (taking the interpreter from the first line)
" F10:   --
" F11:   maximize window
" F12:   yakuake [outside of neovim]
"
" Installation (Ubuntu):
"   The HQ suggests a PPA that contains the development version:
"     * https://github.com/neovim/neovim/wiki/Installing-Neovim#ubuntu
"   If you want to build Neovim from source, here are the steps:
"   1) Visit https://github.com/neovim/neovim and find the tagged version you need.
"      Download the zip, uncompress it, and enter the project folder.
"   2) Install the dependencies:
"      $ sudo apt-get install libtool autoconf automake cmake libncurses5-dev g++
"      Note: cmake is needed for YCM too.
"   3) $ make CMAKE_BUILD_TYPE=Release
"      $ sudo make install
"   On all platforms (update this package frequently):
"     $ sudo pip2/pip3 install neovim -U
" Links:
"   * http://vimcasts.org/ (vimcasts contains 68 free screencasts and 47 articles)
"   * http://vimawesome.com/ (list of awesome plugins)
"   * http://vim.spf13.com/ (it can give you ideas of must-have plugins)
"   * https://realpython.com/blog/python/vim-and-python-a-match-made-in-heaven/
"   * https://unlogic.co.uk/2013/02/08/vim-as-a-python-ide/
" Notes:
"   * nvim --startuptime nvim.log    -> check what makes it slow to load
"   * :map H    -> What is mapped on H ?
"   * :verb set expandtab?    -> if expandtab is not OK, then find out who changed it for the last time (verbose)
"   * :set ft=json    -> treat the file as a json file (even if it has a different extension) [ft: filetype]

" Set up leaders
" <Leader>
let mapleader = ","
" <LocalLeader>
let maplocalleader = "\\"

"
" Tips:
"   gx                -> open URL under cursor in your browser
"   :retab            -> replace TABs with 4 spaces
"   :set filetype?    -> current filetype
"   :edit             -> reload the current file (if it was changed outside of vim)
"
" Help:
"   :h help-context    -> v_ (visual mode commands), etc.
"   :h i_CTRL-Y        -> What does Ctrl-y do in insert mode?
"
" Windows:
"   Ctrl+w =           -> equal size
"   Ctrl+w _           -> maximize window's height (my map: F11)
"
" Moving:
"   reposition the current line:
"     zt  -> zoom to top
"     zz  -> zoom to center
"     zb  -> zoom to bottom
"
" Variables:
"                   (nothing) In a function: local to a function; otherwise: global
"   |buffer-variable|    b:   Local to the current buffer.
"   |window-variable|    w:   Local to the current window.
"   |tabpage-variable|   t:   Local to the current tab page.
"   |global-variable|    g:   Global.
"   |local-variable|     l:   Local to a function.
"   |script-variable|    s:   Local to a |:source|'ed Vim script.
"   |function-argument|  a:   Function argument (only inside a function).
"   |vim-variable|       v:   Global, predefined by Vim.
"

" create the required directories {{{
    silent !mkdir ~/nvim.local > /dev/null 2>&1
    silent !mkdir ~/nvim.local/tmp > /dev/null 2>&1
    silent !mkdir ~/nvim.local/undo > /dev/null 2>&1
" }}}

let g:python_host_prog = '/usr/bin/python2'
let g:python3_host_prog = '/usr/bin/python3'


" Autoinstall vim-plug {{{
    " https://github.com/junegunn/vim-plug
    let s:vim_plug_dir=expand($HOME.'/.config/nvim/autoload')
    if !filereadable(s:vim_plug_dir.'/plug.vim')
        execute '!wget https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim -P '.s:vim_plug_dir
        let s:install_plug=1
    endif
" }}}

call plug#begin('~/nvim.local/plugged')
" BEGIN

" Make sure you use single quotes

" Shorthand notation; fetches https://github.com/junegunn/vim-easy-align
"Plug 'junegunn/vim-easy-align'

" Any valid git URL is allowed
"Plug 'https://github.com/junegunn/vim-github-dashboard.git'


" ====================================================================
" Color schemes
" ====================================================================
Plug 'freeo/vim-kalisi'
Plug 'michalbachowski/vim-wombat256mod'


" ====================================================================
" Visuals
" ====================================================================
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
    " the indentlines will not show up in the cursorline:
    let g:indentLine_concealcursor = ''
    " When I enter insert mode, UltiSnips and YCM are loaded. At that
    " moment the indent lines disappear :( With F5 I can bring them
    " back. For the first time, F5 must be pressed twice, then it
    " toggles the indent lines correctly.
    " nnoremap <F5>  :IndentLinesToggle<cr>
    " let g:indentLine_conceallevel = 0
" }}}


Plug 'elzr/vim-json'
" {{{
    " https://github.com/elzr/vim-json
    " indentLine conceals quotes in json files; this puts them back:
    let g:vim_json_syntax_conceal = 0
" }}}


" ====================================================================
" Completion
" ====================================================================

Plug 'Shougo/deoplete.nvim'
" {{{

    let g:deoplete#enable_at_startup = 1
    if !exists('g:deoplete#omni#input_patterns')
      let g:deoplete#omni#input_patterns = {}
    endif
    " let g:deoplete#disable_auto_complete = 1

    autocmd InsertLeave,CompleteDone * if pumvisible() == 0 | pclose | endif

    " deoplete tab-complete
    inoremap <expr><tab> pumvisible() ? "\<c-n>" : "\<tab>"
    inoremap <expr><S-Tab> pumvisible() ? "\<c-p>" : "\<tab>"

    " omnifuncs
    augroup omnifuncs
      autocmd!
      autocmd FileType css setlocal omnifunc=csscomplete#CompleteCSS
      autocmd FileType html,markdown setlocal omnifunc=htmlcomplete#CompleteTags
      autocmd FileType javascript setlocal omnifunc=javascriptcomplete#CompleteJS
      autocmd FileType python setlocal omnifunc=pythoncomplete#Complete
      autocmd FileType xml setlocal omnifunc=xmlcomplete#CompleteTags
    augroup end
" }}}

Plug 'zchee/deoplete-jedi'

Plug 'zchee/deoplete-clang'
" {{{
    " Settings for deoplete clang
    let g:deoplete#sources#clang#libclang_path = '/usr/lib/x86_64-linux-gnu/libclang-3.8.so.1'
    let g:deoplete#sources#clang#clang_header = '/usr/lib/llvm-3.8/lib/clang'
" }}}

Plug 'tpope/vim-surround'
Plug 'tpope/vim-repeat'
" {{{
    " viw    -> visually select the current word
    "nnoremap <space> viw
    " select the text, press s and type in the surrounding character / tag
    " cs'"    -> (DON'T select the text) change ' to "
    " ds"     -> (DON'T select the text) delete surrounding "
    " dst     -> (DON'T select the text) delete surrounding tags (for ex. <q> and </q>)
    " cs'<q>  -> (DON'T select the text) change ' to <q>...</q>
    " cst'    -> (DON'T select the text) change surrounding tag to '
    " select text, s ]    -> surround with [ and ] (no space)
    " ----------

    " vim-repeat: https://github.com/tpope/vim-repeat
    " However, I didn't understand how to use it...
    " But here I found an excellent example:
    " http://vimcasts.org/episodes/creating-repeatable-mappings-with-repeat-vim/

    " here are some own surroundings that are more intuitive for me
    nnoremap <silent> <Plug>SurroundWordWithApostrophe  viw<esc>a'<esc>hbi'<esc>lel
        \ :call repeat#set("\<Plug>SurroundWordWithApostrophe", v:count)<cr>
    nmap <Leader>'  <Plug>SurroundWordWithApostrophe
    "
    nnoremap <silent> <Plug>SurroundWordWithQuote  viw<esc>a"<esc>hbi"<esc>lel
        \ :call repeat#set("\<Plug>SurroundWordWithQuote", v:count)<cr>
    nmap <Leader>"  <Plug>SurroundWordWithQuote
    "
    nnoremap <silent> <Plug>SurroundWordWithBacktick  viw<esc>a`<esc>hbi`<esc>lel
        \ :call repeat#set("\<Plug>SurroundWordWithBacktick", v:count)<cr>
    nmap <Leader>`  <Plug>SurroundWordWithBacktick
    "
    vnoremap <Leader>'  <esc>`<i'<esc>`>la'<esc>
    vnoremap <Leader>"  <esc>`<i"<esc>`>la"<esc>
    vnoremap <Leader>`  <esc>`<i`<esc>`>la`<esc>
" }}}


" ====================================================================
" Git
" ====================================================================
"Plug 'tpope/vim-fugitive'
" {{{
" }}}

Plug 'airblade/vim-gitgutter'
" {{{
" }}}


" ====================================================================
" Syntax
" ====================================================================
Plug 'neomake/neomake'
" {{{
"    " neomake is async => it doesn't block the editor
"    " It's a syntastic alternative. Syntastic was slow for me on python files.
"    " $ sudo pip2/pip3 install flake8 -U
"    " $ sudo pip2/pip3 install vulture -U
"    let g:neomake_python_enabled_makers = ['flake8', 'pep8', 'vulture']
"    " let g:neomake_python_enabled_makers = ['flake8', 'pep8']
"    " E501 is line length of 80 characters
"    let g:neomake_python_flake8_maker = { 'args': ['--ignore=E115,E266,E501,E302'], }
"    let g:neomake_python_pep8_maker = { 'args': ['--max-line-length=100', '--ignore=E115,E266,E302'], }
"
"    " I had a problem under Manjaro: problems were underlined, instead of coloring red
"    let distro = system("cat /etc/issue | head -1 | cut -f 1 -d ' '")
"    if distro == "Manjaro\n"
"        let g:neomake_highlight_columns = 0
"    endif
"
"    " run neomake on the current file on every write:
    "autocmd! BufWritePost * Neomake

    let g:neomake_python_enabled_makers = ['pylint']

" }}}


" ====================================================================
" Session management
" ====================================================================
Plug 'xolox/vim-misc' | Plug 'xolox/vim-session'
" {{{
    " allows you to save and restore the current session (restart vim)
    " :SaveSession    -> save the session
    " :OpenSession    -> load the saved session
    let g:session_autosave = 'no'
    let g:session_autoload = 'no'
    let g:session_directory = '~/nvim.local/sessions'
" }}}



" ====================================================================
" Appearance
" ====================================================================
"Plug 'bling/vim-airline'
Plug 'vim-airline/vim-airline'
" {{{
" " air-line
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

" unicode symbols
let g:airline_left_sep = '»'
let g:airline_left_sep = '▶'
let g:airline_right_sep = '«'
let g:airline_right_sep = '◀'
let g:airline_symbols.linenr = '¶'
let g:airline_symbols.paste = 'ρ'
let g:airline_symbols.paste = 'Þ'
let g:airline_symbols.paste = '∥'
let g:airline_symbols.whitespace = 'Ξ'
" }}}
Plug 'vim-airline/vim-airline-themes'
" {{{
    " https://github.com/vim-airline/vim-airline
    " let distro = system("cat /etc/issue | head -1 | cut -f 1 -d ' '")
    " if distro == "Manjaro\n"
    "     set termguicolors
    " else
    "     " Ubuntu
    "     set termguicolors
    "     " let $NVIM_TUI_ENABLE_TRUE_COLOR = 1
    " endif
    "set termguicolors
    " also install the system package 'powerline-fonts'
    let g:airline_powerline_fonts = 1
    " Enable the list of buffers
    let g:airline#extensions#tabline#enabled = 1
    " Show just the filename
    let g:airline#extensions#tabline#fnamemod = ':t'

    let g:airline#extensions#tabline#left_sep = ''
    let g:airline#extensions#tabline#left_alt_sep = '|'
" }}}

Plug 'vim-airline/vim-airline-themes'


" ====================================================================
" Buffers
" ====================================================================
Plug 'vim-scripts/BufOnly.vim'
" {{{
    " :BufOnly closes all buffers except the current one
" }}}


" ====================================================================
" Navigation
" ====================================================================.

Plug 'easymotion/vim-easymotion'
" {{{
"    " http://vimawesome.com/plugin/easymotion
"    let g:EasyMotion_do_mapping = 0 " Disable default mappings
"    " Turn on case insensitive feature
"    let g:EasyMotion_smartcase = 1
"    " <Leader>w    -> search word
"    map <Leader>w <Plug>(easymotion-bd-w)
"    " Jump to anywhere you want with minimal keystrokes, with just one key binding.
"    " `s{char}{label}`
"    " nmap s <Plug>(easymotion-overwin-f)
"    " or
"    " `s{char}{char}{label}`
"    " Need one more keystroke, but on average, it may be more comfortable.
"    nmap <Leader>s <Plug>(easymotion-overwin-f2)
"
"    " JK motions: motions (j: down, k: up, l: line, up and down)
"    map <Leader>j <Plug>(easymotion-j)
"    map <Leader>k <Plug>(easymotion-k)
"    map <Leader>l <Plug>(easymotion-bd-jk)
"    " If you want to use more useful mappings, please see :h easymotion.txt for more detail.
" }}}

Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
" {{{
    imap <c-x><c-k> <plug>(fzf-complete-word)
    imap <c-x><c-f> <plug>(fzf-complete-path)
    imap <c-x><c-j> <plug>(fzf-complete-file-ag)
    imap <c-x><c-l> <plug>(fzf-complete-line)
" }}}



Plug 'shougo/unite.vim' | Plug 'shougo/neomru.vim'
" {{{
"    " Ctrl-p    -> since we are used to it
"    " http://vimawesome.com/plugin/unite-vim
"    " https://github.com/shougo/neomru.vim , this is required for file_mru
"    function! s:unite_settings()
"       imap <buffer><tab>           <c-x><c-f>
"       nmap <silent><buffer><esc>   :bd<cr>
"       imap <buffer><c-p>   <Plug>(unite_select_previous_line)
"       imap <buffer><c-n>   <Plug>(unite_select_next_line)
"       inoremap <silent><buffer><expr> <C-s>     unite#do_action('split')
"       inoremap <silent><buffer><expr> <C-v>     unite#do_action('vsplit')
"       " for toggling (show / hide)
"       " imap <silent><buffer><c-l>   <esc>:bd<cr>
"       imap <silent><buffer><c-p>   <esc>:bd<cr>
"       imap <F3>                    <esc>:bd<cr>
"    endfunction
"    " custom mappings for the unite buffer
"    autocmd FileType unite call s:unite_settings()
"
"    " nnoremap <c-p> :Unite file file_rec -start-insert -vertical -direction=botright<cr>
"
"    "nnoremap <Leader>r :<C-u>Unite -start-insert file_rec<cr>
"    nnoremap <c-p> :Unite file file_rec buffer<cr>
"    " nnoremap <c-l> :Unite line<cr>
"    noremap <F3> :Unite file_mru<cr>
" }}}

Plug 'mileszs/ack.vim'
" {{{
    if executable('ag')
      "let g:ackprg = 'ag --vimgrep'
      let g:ackprg = 'ag --nogroup --nocolor --column'
    endif
" }}}


" ====================================================================
" Tags
" ====================================================================
Plug 'majutsushi/tagbar'
" {{{
    " $ yaourt ctags                  # Manjaro
    " $ sudo apt-get install ctags    # Ubuntu
    nnoremap <F4> :TagbarToggle<cr>
" }}}


call plug#end()    " vim-plug




"" these unite lines must be here, after vim-plug, otherwise vim drops an error when launched
"" https://github.com/Shougo/neobundle.vim/issues/330
"" {{{
"    call unite#filters#matcher_default#use(['matcher_fuzzy'])
"    call unite#custom#profile('default', 'context', {
"    \   'prompt': '» ',
"    \   'start_insert': 1,
"    \   'vertical': 1,
"    \   'direction': 'botright',
"    \   'ignorecase': 1
"    \ })
"" }}}



" =================================================================================

" Always show status bar
set laststatus=2
" Let plugins show effects after 500ms, not 4s
set updatetime=500
" Let vim-gitgutter do its thing on large files
let g:gitgutter_max_signs=10000


" If your terminal's background is white (light theme), uncomment the following
" to make EasyMotion's cues much easier to read.
" hi link EasyMotionTarget String
" hi link EasyMotionShade Comment
" hi link EasyMotionTarget2First String
" hi link EasyMotionTarget2Second Statement

" Enable syntax
syntax enable

" Hybrid numbering
set relativenumber showmatch
set number

" Highlight python
let python_highlight_all = 1

" allow backspacing over everything in insert mode
set backspace=indent,eol,start


if has("vms")
  set nobackup      " do not keep a backup file, use versions instead
else
  set backup        " keep a backup file (restore to previous version)
  set undofile      " keep an undo file (undo changes after closing)
endif
set history=50      " keep 50 lines of command line history
set ruler       " show the cursor position all the time
set showcmd     " display incomplete commands
set incsearch       " do incremental searching

" Don't use Ex mode, use Q for formatting
map Q gq

" CTRL-U in insert mode deletes a lot.  Use CTRL-G u to first break undo,
" so that you can undo CTRL-U after inserting a line break.
inoremap <C-U> <C-G>u<C-U>

" In many terminal emulators the mouse works just fine, thus enable it.
if has('mouse')
  set mouse=a
endif

" Only do this part when compiled with support for autocommands.
if has("autocmd")
"
"  " Enable file type detection.
"  " Use the default filetype settings, so that mail gets 'tw' set to 72,
"  " 'cindent' is on in C files, etc.
"  " Also load indent files, to automatically do language-dependent indenting.
"  filetype plugin indent on
"
"  " Put these in an autocmd group, so that we can delete them easily.
"  augroup vimrcEx
"  au!
"
"  " When editing a file, always jump to the last known cursor position.
"  " Don't do it when the position is invalid or when inside an event handler
"  " (happens when dropping a file on gvim).
"  " Also don't do it when the mark is in the first line, that is the default
"  " position when opening a file.
"  autocmd BufReadPost *
"    \ if line("'\"") > 1 && line("'\"") <= line("$") |
"    \   exe "normal! g`\"" |
"    \ endif
"
"  augroup END
"
else

  set autoindent        " always set autoindenting on

endif " has("autocmd")


" Convenient command to see the difference between the current buffer and the
" file it was loaded from, thus the changes you made.
" Only define it when not defined already.
if !exists(":DiffOrig")
  command DiffOrig vert new | set bt=nofile | r ++edit # | 0d_ | diffthis
          \ | wincmd p | diffthis
endif


" ============== Settings =========================
" Indenting the next lines in a scope by 4 spaces
set shiftwidth=4
" Replacing shift with tabs
set expandtab
" Dont know what this do yet,
"set backspace=2,indent,eol,start
" Tab is 4 spaces
set tabstop=4
" Syntax highlight
syntax on
" Highlight search"
set hlsearch
" Case insensitive search
set ignorecase

" Trying to escape modes faster
set timeoutlen=1000 ttimeoutlen=0

" Setting special chars"
set list
set listchars=tab:→\ ,trail:·,extends:>,precedes:<


" Setting visual mode colors"
"hi Visual term=reverse cterm=reverse guibg=Grey

"VimTip 20: Are *.swp and *~ files littering your working directory? {{{
    set backup
    set backupext=~
    set backupdir=~/nvim.local/tmp
    set directory=~/nvim.local/tmp

    " let's add undo
    set undofile
    set undodir=~/nvim.local/undo
" }}}

" automatically change window's cwd to file's dir
set autochdir


" remove trailing whitespaces, strip, trim {{{
"    autocmd BufWritePre *.txt :%s/\s\+$//e
"    autocmd BufWritePre *.py :%s/\s\+$//e
"    autocmd BufWritePre *.scala :%s/\s\+$//e
"    autocmd BufWritePre *.pl :%s/\s\+$//e
"    autocmd BufWritePre *.php :%s/\s\+$//e
"    autocmd BufWritePre *.java :%s/\s\+$//e
"    autocmd BufWritePre *.md :%s/\s\+$//e
"    autocmd BufWritePre *.h :%s/\s\+$//e
"    autocmd BufWritePre *.tex :%s/\s\+$//e
"    autocmd BufWritePre *.vim :%s/\s\+$//e
"    autocmd BufWritePre *.nfo :%s/\s\+$//e
"    autocmd BufWritePre *.json :%s/\s\+$//e
"    autocmd BufWritePre *.rs :%s/\s\+$//e
" }}}


" Setting vim to load local vimrc files
set exrc
set secure


"switch spell check on/off (grammar check)
setlocal spell spelllang=en_us      "let's use English by default
set nospell                         "by default spell is off



" ============== Color scheme =========================

set background=dark
" {{{
    colorscheme kalisi
    " black background:
    hi Normal  ctermbg=Black guifg=#d0d0d0 guibg=Black  gui=none
    " black background at the end of file too (with lines ~):
    hi NonText ctermbg=Black guifg=#958b7f guibg=Black gui=none
" }}}
"colorscheme advantage
"colorscheme elflord
"hi LineNr       term=bold cterm=bold ctermfg=2 guifg=DarkGrey guibg=#334C75
"hi LineNr       term=bold cterm=bold ctermfg=2 guifg=Grey
"guibg=Grey90
"colorscheme PaperColor
"colorscheme wombat256mod
" ================= Keys ===========================

"Allow saving of files as sudo when I forgot to start vim using sudo."
cmap w!! w !sudo tee > /dev/null %

" XML Lint
map @@x !%xmllint --format --recover -^M


"map up/down arrow keys to unimpaired commands
nmap <Up> [e
nmap <Down> ]e
vmap <Up> [egv
vmap <Down> ]egv

"map left/right arrow keys to indendation
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


" VimTip 305: make it easy to update/reload .vimrc {{{
    "src: source rc file
    "erc: edit rc file
    nnoremap <Leader>src :source $MYVIMRC<cr>
    nnoremap <Leader>erc :e $MYVIMRC<cr>
    " nnoremap <Leader>erc :vsplit $MYVIMRC<cr>
" }}}

let g:airline_powerline_fonts = 1
