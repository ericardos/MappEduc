# 🎓 MappEduc - Mapeamento de Projeção Educacional

**Ferramenta livre e leve para educadores explorarem o projection mapping em sala de aula.**

![Licença](https://img.shields.io/badge/Licen%C3%A7a-GPL%20v3-blue.svg)
![Versão](https://img.shields.io/badge/Vers%C3%A3o-2.3-green.svg)
![Status](https://img.shields.io/badge/Status-Est%C3%A1vel-brightgreen.svg)

---

## ✨ Sobre o Projeto

Criado pelo **Prof. Edson Ricardo dos Santos da Silva**, o **MappEduc** nasceu da necessidade de uma ferramenta acessível para o ensino de artes visuais. Permite deformar imagens e vídeos em tempo real, adaptando projeções a superfícies irregulares de forma simples e intuitiva.

**Objetivo:** Ser um recurso educacional livre para que professores e alunos possam explorar o mapeamento de projeção sem custos e com baixa exigência de hardware.

---

## 🚀 Funcionalidades

### 🎯 Mapeamento
- Deformação por grade de pontos de controle (malha de 1x1 a 6x6)
- Zoom e Pan para ajustes precisos
- Mover pontos selecionados ou camadas inteiras com as setas do teclado
- Escala da camada (aumentar/diminuir mantendo proporção)

### 📁 Camadas
- Suporte a múltiplas camadas
- Imagens: JPG, PNG (com transparência nativa)
- Vídeos: MP4, AVI, MOV, MKV, WEBM
- Controle individual de opacidade e visibilidade
- Travar/destravar pontos de controle

### 🎭 Chroma Key (Máscara por Cor)
- Remova cores específicas da imagem (preto, branco, verde, azul, vermelho)
- Controle de tolerância para ajuste fino
- Ideal para remover fundos ou criar recortes

### 📋 Gerenciamento de Camadas
- **Duplicar Camada** (Ctrl+D) - Cria cópia idêntica
- **Substituir Arquivo** - Troca a mídia mantendo todas as deformações
- **Menu de contexto** (clique direito) - Acesso rápido a todas as opções

### 💾 Projetos
- Salvar projeto completo (.mep)
- Carregar projetos salvos
- Inclui todas as deformações, opacidades e configurações

### ⌨️ Desfazer/Refazer
- Ctrl+Z para desfazer
- Ctrl+Shift+Z para refazer

---

## ⌨️ Atalhos de Teclado

| Tecla | Ação |
|:-----:|:-----|
| `V` | Mostrar/Esconder camada |
| `L` | Travar/Destravar pontos de controle |
| `R` | Resetar grid (voltar ao formato original) |
| `F` | Alternar modo Fit/Stretch |
| `S` | Aumentar escala da camada |
| `Shift+S` | Diminuir escala da camada |
| `Ctrl+S` | Resetar escala da camada |
| `Ctrl+D` | Duplicar camada selecionada |
| `Setas` | Mover ponto selecionado OU camada inteira |
| `ESC` | Deselecionar ponto |
| `+ / -` | Zoom in / Zoom out |
| `0` ou `Home` | Resetar visualização (zoom e pan) |
| `F11` | Tela cheia na janela de projeção |
| `Del` | Remover camada selecionada |
| `Ctrl+Z` | Desfazer última ação |
| `Ctrl+Shift+Z` | Refazer ação desfeita |
| `F1` | Ajuda completa |

---

## 🖱️ Controles do Mouse

| Ação | Descrição |
|:-----|:----------|
| **Scroll** | Zoom no ponto do mouse |
| **Botão do meio arrastar** | Pan (mover visualização) |
| **Botão direito arrastar** | Pan (mover visualização) |
| **Arrastar ponto verde** | Deformar a imagem |
| **Arrastar área vazia** | Pan (quando nenhum ponto selecionado) |
| **Duplo clique** | Resetar visualização (zoom 100%, pan zerado) |
| **Clique na camada** | Selecionar camada |
| **Clique direito na camada** | Menu de contexto (duplicar, substituir, máscara, resetar) |

---

## 🔧 Como Instalar e Usar

### 📦 Requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes do Python)

### ⚙️ Instalação das Dependências

```bash
pip install PySide6 PyOpenGL opencv-python numpy
