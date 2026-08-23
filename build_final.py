import subprocess
import sys
import os

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

def main():
    print("=" * 60)
    print("  🏥 Construindo Worklist Analyzer")
    print("=" * 60)
    
    print("\n📦 Verificando/Instalando dependências...")
    run_command(f"{sys.executable} -m pip install --upgrade pyinstaller pillow")
    
    if os.path.exists("pixeon.ico"):
        print("✅ Ícone encontrado!")
        icone = "--icon=pixeon.ico"
        data = "--add-data \"pixeon.ico;.\""
    else:
        print("⚠️ Ícone não encontrado. Continuando sem ícone...")
        icone = ""
        data = ""
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=Worklist_Analyzer_v2.1",
        "--hidden-import=PIL",
        "--hidden-import=PIL._imagingtk",
        "--collect-all=PIL",
        "--clean",
        "--noconfirm"
    ]
    
    if icone:
        cmd.insert(3, icone)
        cmd.insert(4, data)
    
    cmd.append("dicom_analyzer.py")
    
    print("\n🔨 Gerando executável...")
    print("-" * 60)
    
    cmd_str = " ".join(cmd)
    success = run_command(cmd_str)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ BUILD CONCLUÍDO COM SUCESSO!")
        print(f"📁 Executável: {os.getcwd()}\\dist\\Worklist_Analyzer_v2.1")
        print("=" * 60)
        print("\n👉 Teste o executável: dist\\Worklist_Analyzer_v2.1")
    else:
        print("\n" + "=" * 60)
        print("❌ Erro no build. Verifique as mensagens acima.")
        print("=" * 60)
    
    input("\nPressione ENTER para sair...")

if __name__ == "__main__":
    main()