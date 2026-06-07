# 🛰️ MEND — Orbital Debris Detection System

> **Global Solution | Computer Vision com OpenCV**
> Sistema de detecção e rastreamento de debris orbitais em vídeo espacial.

---

## 📌 Descrição da Solução

A **MEND** (*Modular Environmental Network for Debris*) é uma empresa de limpeza orbital cuja solução opera em órbita LEO para capturar e eliminar debris espaciais — reduzindo o tempo de reentrada de detritos de ~80 anos para ~3 anos.

O hardware responsável pela operação é a nave **ORION**, que combina duas tecnologias em uma única plataforma reutilizável:

- 🔵 **Laser de ablação** — vaporiza e desvia debris menores para reentrada atmosférica
- 🟠 **Garra mecânica** — captura fisicamente satélites maiores inoperantes

Este sistema de Visão Computacional simula o módulo de **detecção e triagem de debris** embarcado na ORION:

- **Captura de vídeo** via arquivo de vídeo ou webcam em tempo real
- **Detecção por limiar de brilho** — objetos mais brilhantes que o limiar são identificados como debris (ideal para fundo escuro espacial)
- **Operações morfológicas** para eliminar ruído e isolar os objetos
- **Rastreamento por centróide** com histórico de trajetória e ID único por debris
- **Classificação de risco**: BAIXO / MÉDIO / ALTO / CRÍTICO (baseado no tamanho do objeto)
- **Decisão de ação ORION**: LASER (debris menores) ou GARRA (debris maiores)
- **HUD** com contador de debris em destaque, FPS e telemetria em tempo real

---

## 🧰 Bibliotecas Utilizadas
| Biblioteca | Versão mínima | Uso |
|------------|---------------|-----|
| `opencv-python` | 4.8.0 | Captura, processamento, detecção, HUD |
| `numpy` | 1.24.0 | Operações matriciais |

> Python padrão: `math`, `time`, `collections`

---

## ▶️ Instruções de Execução
### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/mend-orion-orbital-detection.git
cd mend-orion-orbital-detection
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Executar
```bash
python orion_detector.py
```

> O nome do arquivo de vídeo é definido pela constante `VIDEO_PATH` no início do script.
> Para usar a webcam, altere para `VIDEO_PATH = 0`.

### Controles durante a execução

| Tecla | Ação |
|-------|------|
| `Q` | Encerra o sistema |
| `M` | Alterna visualização da máscara de detecção |
| `+` | Aumenta o limiar de brilho (detecta menos objetos) |
| `-` | Diminui o limiar de brilho (detecta mais objetos) |

---

## 🎯 Pipeline de Visão Computacional
```
Captura (arquivo de vídeo ou webcam)
        ↓
Conversão para escala de cinza
        ↓
Threshold por brilho (THRESH_BINARY)
        ↓
Operações Morfológicas (Open + Close)
        ↓
Detecção de Contornos (findContours)
        ↓
Filtragem por Área (min/max debris)
        ↓
Rastreamento por Centróide (ID único por debris)
        ↓
Classificação de Risco + Decisão de Ação ORION
        ↓
Renderização HUD + trilha de movimento
```

---

## 📁 Estrutura do Projeto
```
mend-orion-orbital-detection/
├── orion_detector.py  # Sistema principal
├── debris_v1.mp4      # Vídeo de demonstração
├── requirements.txt   # Dependências
└── README.md          # Este arquivo
```

---

## 👥 Integrantes
| Nome | RM |
|------|----|
| Fabiano | RM555524 |
| Lorran | RM558982 |
| Maria | RM557478 |
| Pedro | RM556268 |
| Vinícius | RM555200 |

---

## 📄 Contexto — Global Solution FIAP
Este projeto foi desenvolvido como parte da **Global Solution** da FIAP, aplicando Visão Computacional ao contexto da solução **MEND** de limpeza orbital — operacionalizada pela nave **ORION** — como resposta ao crescente problema do lixo espacial em órbita LEO.
