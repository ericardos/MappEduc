#!/bin/bash

# =============================================================================
# MappEduc - Script de Execução para Linux/macOS
# =============================================================================
# Autor: Edson Ricardo dos Santos da Silva
# Licença: GNU General Public License v3.0
# Versão: 2.3
# =============================================================================

clear

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                 ║"
echo "║              🎓 MAPPEDUC - Mapeamento de Projeção               ║"
echo "║                    Ferramenta Educacional Livre                  ║"
echo "║                         Versão 2.3                              ║"
echo "║                                                                 ║"
echo "║           Autor: Edson Ricardo dos Santos da Silva              ║"
echo "║           Licença: GNU General Public License v3.0              ║"
echo "║                                                                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# =========================
# CONFIGURAÇÕES
# =========================
APP="mappeduc.py"
VENV_DIR="venv"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =========================
# FUNÇÕES AUXILIARES
# =========================
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# =========================
# VERIFICAR PYTHON
# =========================
if ! command -v python3 &> /dev/null; then
    print_error "Python3 não encontrado."
    echo ""
    echo "📦 Instale com um dos comandos abaixo:"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "   Fedora:        sudo dnf install python3 python3-virtualenv python3-pip"
    echo "   Arch:          sudo pacman -S python python-virtualenv python-pip"
    echo ""
    echo "Pressione ENTER para sair..."
    read
    exit 1
fi

print_success "Python3 encontrado: $(python3 --version)"

# =========================
# VERIFICAR ARQUIVO PRINCIPAL
# =========================
if [ ! -f "$APP" ]; then
    print_error "Arquivo '$APP' não encontrado."
    echo "   Certifique-se de que o script está na pasta raiz do MappEduc."
    echo ""
    echo "Pressione ENTER para sair..."
    read
    exit 1
fi

# =========================
# CRIAR VENV SE NÃO EXISTIR
# =========================
if [ ! -d "$VENV_DIR" ]; then
    print_info "Criando ambiente virtual..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        print_error "Falha ao criar ambiente virtual."
        echo "   Verifique se o módulo venv está instalado:"
        echo "   sudo apt install python3-venv"
        echo ""
        echo "Pressione ENTER para sair..."
        read
        exit 1
    fi
    print_success "Ambiente virtual criado."
fi

# =========================
# ATIVAR VENV (forma compatível)
# =========================
print_info "Ativando ambiente virtual..."

if [ -f "$VENV_DIR/bin/activate" ]; then
    # Linux/macOS
    . "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    # Windows (Git Bash, WSL)
    . "$VENV_DIR/Scripts/activate"
else
    print_error "Não foi possível encontrar o script de ativação do venv."
    echo ""
    echo "Pressione ENTER para sair..."
    read
    exit 1
fi

if [ $? -ne 0 ]; then
    print_error "Falha ao ativar ambiente virtual."
    echo ""
    echo "Pressione ENTER para sair..."
    read
    exit 1
fi

print_success "Ambiente virtual ativado."

# =========================
# INSTALAR DEPENDÊNCIAS
# =========================
print_info "Verificando dependências..."

# Atualizar pip
pip install --upgrade pip --quiet 2>/dev/null

# Instalar dependências
echo "   Instalando pacotes necessários..."
pip install PySide6 PyOpenGL opencv-python numpy --quiet

if [ $? -ne 0 ]; then
    print_warning "Alguns pacotes podem não ter sido instalados corretamente."
    echo "   Tentando instalar novamente com mais detalhes..."
    pip install PySide6 PyOpenGL opencv-python numpy
fi

print_success "Dependências verificadas."

# =========================
# CONFIGURAÇÕES DO SISTEMA
# =========================
export QT_QPA_PLATFORM=xcb
export LIBGL_ALWAYS_SOFTWARE=0
export vblank_mode=0

# =========================
# EXIBIR DICAS
# =========================
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                        ⌨️  ATALHOS PRINCIPAIS                    ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║  V       - Mostrar/Esconder camada                              ║"
echo "║  L       - Travar/Destravar pontos                              ║"
echo "║  R       - Resetar grid                                         ║"
echo "║  S       - Aumentar escala da camada                            ║"
echo "║  Ctrl+D  - Duplicar camada                                      ║"
echo "║  Setas   - Mover ponto ou camada inteira                        ║"
echo "║  F11     - Tela cheia (projeção)                                ║"
echo "║  F1      - Ajuda completa                                       ║"
echo "║  Ctrl+Z  - Desfazer                                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

print_info "Iniciando MappEduc v2.3..."
echo "   (Pode levar alguns segundos na primeira execução)"
echo ""

# =========================
# EXECUTAR APLICAÇÃO
# =========================
python3 "$APP"

# =========================
# FINALIZAR
# =========================
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_success "MappEduc finalizado. Obrigado por usar!"
else
    print_warning "MappEduc finalizado com código: $EXIT_CODE"
    echo ""
    echo "Se o programa não abriu, tente executar manualmente:"
    echo "   source venv/bin/activate"
    echo "   python3 mappeduc.py"
fi

# Desativar ambiente virtual
deactivate 2>/dev/null

echo ""
echo "Pressione ENTER para sair..."
read
exit $EXIT_CODE
