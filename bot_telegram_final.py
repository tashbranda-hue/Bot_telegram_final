import time
import pandas as pd
import yfinance as yf
import ta
import requests
from datetime import datetime

# --- CONFIGURATION ---
TOKEN = "8530916878:AAFiJ-J5yVj6e1zMcNHi_lDevA0-VzZQorY"
CHAT_ID = "8631771945"
portefeuille = {'EURUSD=X': 0.00015, 'GC=F': 0.10}

# Mémoire des alertes pour éviter les spams
derniere_alerte = {ticker: None for ticker in portefeuille}

def envoyer_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # Ajout du parse_mode Markdown pour un formatage propre (gras, etc.)
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        # Utilisation de json=payload pour que le Markdown soit bien interprété par l'API Telegram
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erreur envoi Telegram : {e}")

def verifier_marche():
    print(f"--- Scan : {datetime.now().strftime('%H:%M')} ---")
    for ticker in portefeuille:
        try:
            df = yf.download(ticker, period='5d', interval='1h', progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.droplevel(1)
            
            if df.empty:
                continue

            high_band = df['High'].rolling(window=20).max().iloc[-2]
            low_band = df['Low'].rolling(window=20).min().iloc[-2]
            prix_actuel = df['Close'].iloc[-1]
            
            signal = None
            sl = 0.0
            tp = 0.0
            
            # --- LOGIQUE D'ENTRÉE ET DE RISQUE (DONCHIAN) ---
            if prix_actuel > high_band:
                signal = "LONG"
                sl = low_band # Stop loss sur la bande basse
                distance_risque = abs(prix_actuel - sl)
                tp = prix_actuel + (distance_risque * 2.0) # Ratio 1:2
                
            elif prix_actuel < low_band:
                signal = "SHORT"
                sl = high_band # Stop loss sur la bande haute
                distance_risque = abs(sl - prix_actuel)
                tp = prix_actuel - (distance_risque * 2.0) # Ratio 1:2
                
            else:
                signal = "NEUTRE"
                
            # --- GESTION DES ALERTES ---
            if signal != derniere_alerte[ticker]:
                if signal != "NEUTRE":
                    icone = "💶" if "EUR" in ticker else "🥇"
                    
                    msg = (f"{icone} *SIGNAL BREAKOUT ({ticker})*\n"
                           f"🔹 Action : `{signal}`\n"
                           f"🔹 Prix d'entrée approx : `{prix_actuel:.4f}`\n"
                           f"🛑 Stop Loss (Canal) : `{sl:.4f}`\n"
                           f"🎯 Take Profit (Ratio 1:2) : `{tp:.4f}`")
                    
                    print(f"🚀 Nouveau signal {signal} sur {ticker}")
                    envoyer_telegram(msg)
                else:
                    print(f"Sortie de position ou zone neutre sur {ticker}")
                
                derniere_alerte[ticker] = signal
                
        except Exception as e:
            print(f"⚠️ Erreur lors de l'analyse de {ticker} : {e}")

# --- BOUCLE PRINCIPALE ---
print("🤖 Bot Donchian (EURUSD / XAUUSD) actif avec alertes enrichies...")
envoyer_telegram("🟢 *Démarrage du Bot Donchian (EURUSD & Gold)*\nSystème de cassure H1 activé et en attente de signaux.")

try:
    while True:
        verifier_marche()
        # Pause de 1 heure (3600 secondes)
        time.sleep(3600)
except KeyboardInterrupt:
    print("Bot arrêté manuellement.")

