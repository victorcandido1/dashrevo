"""
Script de teste para upload de planilha
Testa se o erro de comparação float/str foi corrigido
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from data_processor import DataProcessor

def test_upload(file_path):
    """Testa o upload de uma planilha"""
    print("="*60)
    print("TESTE DE UPLOAD DE PLANILHA")
    print("="*60)
    print(f"\nArquivo: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"\n[ERRO] Arquivo nao encontrado: {file_path}")
        return False
    
    try:
        print("\n1. Carregando dados...")
        processor = DataProcessor(file_path)
        
        if processor.df_all is None:
            print("[ERRO] Dados nao foram carregados")
            return False
        
        print(f"[OK] Dados carregados: {len(processor.df_all)} registros")
        
        print("\n2. Verificando colunas numéricas...")
        numeric_cols = ['Revenue', 'Pax', 'Flight_Time_Hours', 'Sheet_Month']
        for col in numeric_cols:
            if col in processor.df_all.columns:
                dtype = processor.df_all[col].dtype
                print(f"  - {col}: {dtype}")
                # Verificar se há valores não numéricos
                non_numeric = processor.df_all[col].apply(lambda x: not isinstance(x, (int, float)) and pd.notna(x))
                if non_numeric.any():
                    print(f"    [AVISO] Encontrados valores nao numericos em {col}")
        
        print("\n3. Aplicando filtros...")
        try:
            processor.initialize_filters()
            print("  [OK] Filtros inicializados")
        except Exception as e:
            print(f"  [ERRO] ao inicializar filtros: {type(e).__name__}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
        
        try:
            processor.apply_filters()
            print("  [OK] Filtros aplicados")
        except Exception as e:
            print(f"  [ERRO] ao aplicar filtros: {type(e).__name__}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
        
        if processor.df_filtered is None:
            print("[ERRO] Filtros nao foram aplicados")
            return False
        
        print(f"[OK] Filtros aplicados: {len(processor.df_filtered)} registros apos filtro")
        
        print("\n4. Testando comparações numéricas...")
        # Testar algumas comparações que poderiam causar erro
        if 'Revenue' in processor.df_filtered.columns:
            test_revenue = processor.df_filtered['Revenue'] > 0
            print(f"  [OK] Comparacao Revenue > 0: OK ({test_revenue.sum()} registros)")
        
        if 'Pax' in processor.df_filtered.columns:
            test_pax = processor.df_filtered['Pax'] >= 0
            print(f"  [OK] Comparacao Pax >= 0: OK ({test_pax.sum()} registros)")
        
        if 'Sheet_Month' in processor.df_filtered.columns:
            test_month = processor.df_filtered['Sheet_Month'] > 0
            print(f"  [OK] Comparacao Sheet_Month > 0: OK ({test_month.sum()} registros)")
        
        print("\n" + "="*60)
        print("[OK] TESTE CONCLUIDO COM SUCESSO!")
        print("="*60)
        return True
        
    except TypeError as e:
        if "'<' not supported" in str(e) or "'>' not supported" in str(e):
            print(f"\n[ERRO] Comparacao entre tipos incompatíveis ainda ocorre!")
            print(f"   Detalhes: {str(e)}")
            return False
        else:
            raise
    except Exception as e:
        print(f"\n[ERRO] {type(e).__name__}: {str(e)}")
        import traceback
        print("\nTraceback completo:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    import pandas as pd
    
    # Caminho da planilha
    file_path = r"C:\Users\User\Downloads\REVO - Flight Hours Control - 2025 v2.1.xlsx"
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    success = test_upload(file_path)
    sys.exit(0 if success else 1)

