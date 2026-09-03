import subprocess
import sys
import os
import shutil
from pathlib import Path

def run_command(cmd):
    """Executa um comando e mostra a saída"""
    print(f"Executando: {cmd}")
    print("-" * 60)
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0

def clean_build():
    """Remove pastas de build anteriores"""
    folders = ["build", "dist", "__pycache__"]
    files = ["*.spec"]
    
    for folder in folders:
        if os.path.exists(folder):
            print(f"🗑️ Removendo: {folder}")
            shutil.rmtree(folder)
    
    for pattern in files:
        for file in Path(".").glob(pattern):
            print(f"🗑️ Removendo: {file}")
            file.unlink()

def main():
    print("=" * 60)
    print("  🏥 DICOM Worklist Analyzer - Build")
    print("  v18.0.0 - Tags 100% Seguras")
    print("=" * 60)
    
    # ============================================================
    # 1. Verificar/Instalar dependências
    # ============================================================
    print("\n📦 Verificando/Instalando dependências...")
    print("-" * 60)
    
    dependencies = [
        "pyinstaller",
        "pillow",  # Para ícones
    ]
    
    for dep in dependencies:
        print(f"  📥 Instalando: {dep}")
        run_command(f"{sys.executable} -m pip install --upgrade {dep}")
    
    # ============================================================
    # 2. Verificar arquivos necessários
    # ============================================================
    print("\n📁 Verificando arquivos do projeto...")
    print("-" * 60)
    
    arquivo_principal = "dicom_analyzer.py"
    icone = "icon.ico"
    
    if not os.path.exists(arquivo_principal):
        print(f"❌ Arquivo principal não encontrado: {arquivo_principal}")
        print("   Verifique se você está na pasta correta.")
        input("\nPressione ENTER para sair...")
        return
    
    if os.path.exists(icone):
        print(f"✅ Ícone encontrado: {icone}")
        icone_arg = f"--icon={icone}"
        data_arg = f"--add-data \"{icone};.\""
    else:
        print(f"⚠️ Ícone não encontrado: {icone}")
        print("   Continuando sem ícone...")
        icone_arg = ""
        data_arg = ""
    
    # ============================================================
    # 3. Limpar builds anteriores
    # ============================================================
    print("\n🧹 Limpando builds anteriores...")
    print("-" * 60)
    clean_build()
    
    # ============================================================
    # 4. Versão do build
    # ============================================================
    from datetime import datetime
    data_atual = datetime.now().strftime("%d.%m.%Y")
    versao = f"Worklist_Analyzer_v18.9.0"
    
    print(f"\n📌 Versão: {versao}")
    
    # ============================================================
    # 5. Montar comando PyInstaller
    # ============================================================
    print("\n🔨 Gerando executável...")
    print("-" * 60)
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--name={versao}",
        "--clean",
        "--noconfirm"
    ]
    
    # Adicionar ícone se existir
    if icone_arg:
        cmd.append(icone_arg)
        cmd.append(data_arg)
    
    # Adicionar hidden imports
    cmd.append("--hidden-import=PIL")
    cmd.append("--hidden-import=PIL._imagingtk")
    
    # Adicionar arquivo principal
    cmd.append(arquivo_principal)
    
    # ============================================================
    # 6. Executar build
    # ============================================================
    cmd_str = " ".join(cmd)
    print(f"🚀 Comando: {cmd_str}")
    print("-" * 60)
    
    success = run_command(cmd_str)
    
    # ============================================================
    # 7. Resultado
    # ============================================================
    if success:
        print("\n" + "=" * 60)
        print("✅ BUILD CONCLUÍDO COM SUCESSO!")
        print("=" * 60)
        print(f"📁 Executável: {os.getcwd()}\\dist\\{versao}.exe")
        print(f"📁 Pasta: {os.getcwd()}\\dist\\")
        print("=" * 60)
        print("\n📝 INSTRUÇÕES:")
        print("  1. O arquivo .exe está na pasta 'dist'")
        print("  2. O ícone 'pixeon.ico' NÃO precisa estar junto do .exe")
        print("  3. O DCMTK deve estar instalado no computador de destino")
        print("  4. O usuário pode configurar o caminho do DCMTK na interface")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Erro no build. Verifique as mensagens acima.")
        print("=" * 60)
    
    input("\n⏎ Pressione ENTER para sair...")

if __name__ == "__main__":
    main()