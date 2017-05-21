"   __     ___              ____             __ _
"   \ \   / (_)_ __ ___    / ___|___  _ __  / _(_) __ _
"    \ \ / /| | '_ ` _ \  | |   / _ \| '_ \| |_| |/ _` |
"     \ V / | | | | | | | | |__| (_) | | | |  _| | (_| |
"      \_/  |_|_| |_| |_|  \____\___/|_| |_|_| |_|\__, |
"                                                 |___/
"
" Place of this configuration file:
"   ~/.config/nvim/init.vim


" Set up leaders:
" <Leader>
let mapleader = ","
" <LocalLeader>
let maplocalleader = "\\"

" Create the required directories
" {{{
    silent !mkdir ~/nvim.local > /dev/null 2>&1
    silent !mkdir ~/nvim.local/tmp > /dev/null 2>&1
    silent !mkdir ~/nvim.local/undo > /dev/null 2>&1
" }}}

" Setting python hosts location, this is needed for some of the plugins
" Mainly Shougos plugins (deoplete, denite)
let g:python_host_prog = '/usr/bin/python2'
let g:python3_host_prog = '/usr/bin/python3'

" Autoinstall vim-plug
" {{{
    " https://github.com/junegunn/vim-plug
    let s:vim_plug_dir=expand($HOME.'/.config/nvim/autoload')
    if !filereadable(s:vim_plug_dir.'/plug.vim')
        execute '!wget https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim -P '.s:vim_plug_dir
        let s:install_plug=1
    endif
" }}}

" This is the start of the plugins list
call plug#begin('~/nvim.local/plugged')

" ====================================================================
" Color schemes
" ====================================================================

Plug 'freeo/vim-kalisi'
Plug 'michalbachowski/vim-wombat256mod'
Plug 'joshdick/onedark.vim'
Plug 'chriskempson/base16-vim'


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
    " the indentlines will not show up in the cursorline:
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

" Dark powered async autocomplete
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

" Adding autocomplete support for python
Plug 'zchee/deoplete-jedi'

" Auto complete support for c based languages
Plug 'zchee/deoplete-clang'
" {{{
    " Settings for deoplete clang
    let g:deoplete#sources#clang#libclang_path = '/usr/lib/x86_64-linux-gnu/libclang-3.5.so.1'
    let g:deoplete#sources#clang#clang_header = '/usr/lib/llvm-3.8/lib/clang'
" }}}

" Add ability to surround given strings with characters
Plug 'tpope/vim-surround'

" Add dot repeat function to tpope plugins
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

" Automatic closing of quotes, parenthesis, brackets, etc.
Plug 'Raimondi/delimitMate'
" {{{
" }}}

" ====================================================================
" Git
" ====================================================================
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

" Unimpaired adds various shortcuts
Plug 'tpope/vim-unimpaired'
" {{{
" }}}

" Comment stuff out
Plug 'tpope/vim-commentary'
" {{{
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
" Plug 'bling/vim-airline'
Plug 'vim-airline/vim-airline'
" {{{
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

" Vim HardTime make it hard to use vim anti-patterns (Like using j to go down
" lines)
Plug 'takac/vim-hardtime'
" {{{
    let g:hardtime_default_on = 1
    let g:hardtime_showmsg = 1
" }}}


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

    " Setting an easymotion search
    map s  <Plug>(easymotion-sn)
    omap s <Plug>(easymotion-tn)

    " These `n` & `N` mappings are options. You do not have to map `n` & `N` to EasyMotion.
    " Without these mappings, `n` & `N` works fine. (These mappings just provide
    " different highlight method and have some other features )
    "map  n <Plug>(easymotion-next)
    "map  N <Plug>(easymotion-prev)

" }}}

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
noremap <silent><expr> <Space>/ incsearch#go(<SID>config_easyfuzzymotion())

" Most Recent Used for fzf
Plug 'lvht/fzf-mru'
" {{{
    " set max lenght for the mru file list
    let g:fzf_mru_file_list_size = 10 " default value
    " set path pattens that should be ignored
    let g:fzf_mru_ignore_patterns = 'fugitive\|\.git/\|\_^/tmp/' " default value
" }}}

Plug 'junegunn/fzf', { 'dir': '~/.fzf', 'do': './install --all' }
Plug 'junegunn/fzf.vim'
" {{{

    " [Tags] Command to generate tags file
    let g:fzf_tags_command = 'ctags -R'


    imap <c-x><c-k> <plug>(fzf-complete-word)
    imap <c-x><c-f> <plug>(fzf-complete-path)
    imap <c-x><c-j> <plug>(fzf-complete-file-ag)
    imap <c-x><c-l> <plug>(fzf-complete-line)

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
" }}}


" Plug 'shougo/unite.vim' | Plug 'shougo/neomru.vim'
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

" Ack lets you search files
" Disabled because using fzf, which also uses ag
" "Plug 'mileszs/ack.vim'
" " {{{
"    if executable('ag')
"      "let g:ackprg = 'ag --vimgrep'
"      let g:ackprg = 'ag --nogroup --nocolor --column'
"    endif
" " }}}

Plug 'Shougo/denite.nvim'
" {{{
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

" ====================================================================
" VimWiki
" ====================================================================

Plug 'vimwiki/vimwiki'
" {{{
" }}}


call plug#end()    " vim-plug




" " these unite lines must be here, after vim-plug, otherwise vim drops an error when launched
" " https://github.com/Shougo/neobundle.vim/issues/330
" " {{{
"    call unite#filters#matcher_default#use(['matcher_fuzzy'])
"    call unite#custom#profile('default', 'context', {
"    \   'prompt': '» ',
"    \   'start_insert': 1,
"    \   'vertical': 1,
"    \   'direction': 'botright',
"    \   'ignorecase': 1
"    \ })
" " }}}



" ====================================================================

" Always show status bar
set laststatus=2
" Let plugins show effects after 500ms, not 4s
set updatetime=500
" Let vim-gitgutter do its thing on large files
let g:gitgutter_max_signs=10000


" If your terminal's background is white (light theme), uncomment the following
" To make EasyMotion's cues much easier to read.
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

" Allow backspacing over everything in insert mode
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

" Tabs are expanded to spaces
set expandtab

" Dont know what this do yet,
" set backspace=2,indent,eol,start

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
" hi Visual term=reverse cterm=reverse guibg=Grey

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


" Setting vim to load local vimrc files
set exrc
set secure


" Switch spell check on/off (grammar check)
setlocal spell spelllang=en_us      "let's use English by default
set nospell                         "by default spell is off



" ============== Color scheme =========================

" set background=dark
" {{{
    colorscheme kalisi
    " {{{
        " black background:
        hi Normal  ctermbg=Black guifg=#d0d0d0 guibg=Black  gui=none
        " black background at the end of file too (with lines ~):
        hi NonText ctermbg=Black guifg=#d0d0d0 guibg=Black gui=none
        " black background:
        hi Normal  ctermbg=Black guifg=#d0d0d0 guibg=Black  gui=none
        " black background at the end of file too (with lines ~):
        hi NonText ctermbg=Black guifg=#d0d0d0 guibg=Black gui=none
    " }}}
    "colorscheme onedark
    " {{{
        "set background=dark
    " }}}
" }}}
" colorscheme advantage
" colorscheme elflord
" hi lineNr       term=bold cterm=bold ctermfg=2 guifg=DarkGrey guibg=#334C75
" hi lineNr       term=bold cterm=bold ctermfg=2 guifg=Grey
" guibg=Grey90
" colorscheme PaperColor
" colorscheme wombat256mod
" ================= Keys ===========================

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


" VimTip 305: make it easy to update/reload .vimrc
" {{{
    "src: source rc file
    "erc: edit rc file
    nnoremap <Leader>src :source $MYVIMRC<cr>
    nnoremap <Leader>erc :e $MYVIMRC<cr>
    " nnoremap <Leader>erc :vsplit $MYVIMRC<cr>
" }}}

" Counting all occurances under cursor
map ,* *<C-O>:%s///gn<CR>


" Setting C-l to denite
nnoremap <C-l> :Denite file file_rec buffer file_mru everything<CR>

" This block sets tmux activity to off, since for some reason NeoVim causes an
" activity when leaving the pane
if exists('$TMUX')

    augroup tmux_no_activity
        autocmd!
        autocmd VimEnter * !tmux set-window-option monitor-activity off
        autocmd VimLeave * !tmux set-window-option monitor-activity on
    augroup end

endif

