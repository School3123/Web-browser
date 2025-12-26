# Simple Python Browser on GitHub Codespaces

GitHub Codespaces上でPython製のGUIブラウザを動かすための手順書です。

## ⚠️ 重要な事前準備 (Codespacesの設定)

Codespacesは通常、画面のない(CUI)環境ですが、ブラウザを表示するには**デスクトップ環境(GUI)**が必要です。
以下の手順で環境をセットアップしてください。

1. Codespacesの画面左下にある `><` (リモート) アイコンをクリックするか、`F1` キーを押してコマンドパレットを開きます。
2. **"Codespaces: Add Dev Container Configuration Files..."** を選択します。
3. **"Modify your active configuration..."** を選択します。
4. 設定画面が進んだら、**"Features"** の選択画面で以下を検索してチェックを入れます。
   - **Desktop Lite** (fluxboxなどを含む軽量デスクトップ環境)
5. **OK** を押し、**"Rebuild now"** (コンテナの再構築) を実行します。
   - これには数分かかります。

---

## 🚀 実行手順

再構築が完了したら、以下の手順で実行します。

### 1. デスクトップ環境の表示
Codespacesが再起動した後：
1. **「ポート (Ports)」** タブを開きます。
2. ポート **6080** (noVNC) が表示されているはずです。
3. 地球儀アイコン（**Open in Browser**）をクリックします。
4. 新しいタブでLinuxのデスクトップ画面が表示されます。

### 2. 依存ライブラリのインストール
**デスクトップ画面の中にあるターミナル** (Terminal Emulator) を開き、以下のコマンドを実行してライブラリをインストールします。

```bash
sudo apt-get update
sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtwebengine
