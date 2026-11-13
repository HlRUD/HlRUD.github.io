pkg update -y && pkg upgrade -y

pkg install python git -y

python -m pip install --upgrade pip

git clone --filter=blob:none --no-checkout https://github.com/HlRUD/HlRUD.github.io.git

cd HlRUD.github.io

git sparse-checkout init --cone

git sparse-checkout set self-splus

git checkout

cd self-splus

python -m pip install splusthon

python self.py
