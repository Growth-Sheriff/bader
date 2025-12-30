#!/bin/bash

# BADER Derneği - Çalıştırma Script'i (Linux/Mac)

# Sanal ortam varsa aktifleştir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Programı çalıştır
python3 main.py


