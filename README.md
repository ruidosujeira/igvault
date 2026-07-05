# igvault

**CLI simples, limpo e confiável para baixar Reels públicos do Instagram.**

Foco exclusivo em Reels públicos. Zero login. Anti-ban forte ativado por padrão.

![Demo](assets/igvault-demo.gif)

*Demo gerada com [VHS](https://github.com/charmbracelet/vhs) do Charmbracelet.*

## ✨ Recursos

- Baixa Reels de qualquer perfil público (`@usuario`)
- Pastas organizadas: `./downloads/@username/reels/`
- Arquivos `.mp4` válidos e reproduzíveis
- Delays humanizados (3-9s), headers stealth mobile + browser
- Rate limiting e cooldown entre perfis
- `--dry-run` para testar instantaneamente
- CLI linda com Rich (cores, progresso, painéis)
- Comandos intuitivos: `reels`, `profile`, `bulk`

## 📦 Instalação

```bash
# 1. Clone ou baixe o projeto
cd igvault

# 2. Instale em modo editável (recomendado)
pip install -e .

# Ou rode diretamente com módulo
python3 -m igvault.cli --help
```

## 🚀 Uso

### Baixar Reels de um perfil

```bash
# Até 10 reels (padrão)
igvault reels @nasa

# Limitar quantidade
igvault reels @instagram --limit 5

# Alias 'profile'
igvault profile nasa --limit 3

# Teste sem baixar nada (recomendado primeiro)
igvault reels @nasa --limit 5 --dry-run
```

### Bulk (vários perfis)

Crie um arquivo `perfis.txt`:

```
nasa
instagram
# comentários são ignorados
nasa
```

```bash
igvault bulk perfis.txt --limit 4
igvault bulk perfis.txt --limit 4 --dry-run
```

### Ajuda

```bash
igvault --help
igvault reels --help
igvault bulk --help
```

## 📁 Estrutura de saída

```
downloads/
└── @nasa/
    └── reels/
        ├── Cxyz1234.mp4
        ├── Cabc9876.mp4
        └── ...
```

## 🛡️ Anti-ban (sempre ativo)

- Delays aleatórios entre 3 e 9.5 segundos
- User-Agents mobile realistas + headers completos
- Cooldown de 10-18s entre diferentes perfis no bulk
- Sem cookies/login — só conteúdo público
- Follow redirects + timeouts seguros

## ✅ Requisitos

- Python 3.10+
- httpx, rich, typer

Instalação automática via `pip install -e .`

## ⚠️ Avisos importantes

- Apenas perfis **públicos**
- Use com responsabilidade
- Instagram pode mudar a qualquer momento (o projeto usa métodos web públicos)
- Para uso pesado considere proxies ou intervalos maiores

## 🧪 Teste rápido (macOS)

```bash
pip install -e .
igvault reels @instagram --limit 2 --dry-run
igvault reels @nasa --limit 1
```

Os arquivos salvos devem abrir normalmente no QuickTime / VLC.

---

Feito para ser simples, robusto e funcionar de primeira.
