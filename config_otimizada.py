from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import json
import os

# =============================================================================
# CONFIGURAÇÕES DE MATERIAIS
# =============================================================================

@dataclass
class PropriedadesMaterial:
    """Propriedades termofísicas de um material"""
    nome: str
    k: float  # Condutividade térmica [W/m·K]
    rho: float  # Densidade [kg/m³]
    cp: float  # Calor específico [J/kg·K]
    k_min: float  # Faixa mínima de k
    k_max: float  # Faixa máxima de k
    temp_max: float  # Temperatura máxima de operação [°C]
    custo_relativo: float  # Custo relativo (1-10)

# Base de dados melhorada de materiais
MATERIAIS_OTIMIZADOS = {
    "aluminio": PropriedadesMaterial(
        nome="Alumínio",
        k=222.0,  # Valor otimizado baseado na correção
        rho=2700.0,
        cp=900.0,
        k_min=200.0,
        k_max=250.0,
        temp_max=500.0,
        custo_relativo=3.0
    ),
    "cobre": PropriedadesMaterial(
        nome="Cobre",
        k=401.0,
        rho=8960.0,
        cp=385.0,
        k_min=380.0,
        k_max=410.0,
        temp_max=800.0,
        custo_relativo=8.0
    ),
    "aco_inoxidavel": PropriedadesMaterial(
        nome="Aço Inoxidável",
        k=16.0,
        rho=8000.0,
        cp=500.0,
        k_min=14.0,
        k_max=20.0,
        temp_max=1000.0,
        custo_relativo=5.0
    ),
    "ferro": PropriedadesMaterial(
        nome="Ferro",
        k=80.0,
        rho=7870.0,
        cp=450.0,
        k_min=70.0,
        k_max=90.0,
        temp_max=900.0,
        custo_relativo=2.0
    )
}

# =============================================================================
# CONFIGURAÇÕES DE VALIDAÇÃO FÍSICA
# =============================================================================

@dataclass
class LimitesValidacao:
    """Limites físicos para validação de parâmetros"""
    
    # Temperaturas [°C]
    temp_min: float = -273.15  # Zero absoluto
    temp_max: float = 3000.0   # Limite prático
    temp_alerta_baixa: float = -200.0
    temp_alerta_alta: float = 1500.0
    
    # Dimensões [m]
    dimensao_min: float = 1e-6  # 1 micrometro
    dimensao_max: float = 100.0  # 100 metros
    dimensao_alerta_pequena: float = 1e-4
    dimensao_alerta_grande: float = 10.0
    
    # Coeficientes de convecção [W/m²·K]
    h_min: float = 0.1
    h_max: float = 50000.0
    h_alerta_baixo: float = 1.0
    h_alerta_alto: float = 10000.0
    
    # Condutividade térmica [W/m·K]
    k_min: float = 0.01
    k_max: float = 1000.0
    k_alerta_baixa: float = 0.1
    k_alerta_alta: float = 500.0

# =============================================================================
# CONFIGURAÇÕES DE PERFORMANCE
# =============================================================================

@dataclass
class ConfigPerformance:
    """Configurações de otimização de performance"""
    
    # Cache
    cache_ttl_segundos: int = 3600  # 1 hora
    cache_max_items: int = 1000
    cache_auto_cleanup: bool = True
    
    # Cálculos numéricos
    precisao_numerica: int = 6
    max_iteracoes: int = 1000
    tolerancia_convergencia: float = 1e-6
    
    # Processamento paralelo
    usar_multiprocessing: bool = False
    max_processos: int = 4
    
    # Logging
    nivel_log: str = "INFO"
    salvar_logs: bool = True
    arquivo_log: str = "sistema_calor.log"
    
    # Monitoramento
    monitor_performance: bool = True
    salvar_metricas: bool = True

# =============================================================================
# CONFIGURAÇÕES DE INTERFACE
# =============================================================================

@dataclass
class ConfigInterface:
    """Configurações da interface web e gráficos"""
    
    # Flask
    debug_mode: bool = True
    port: int = 5000
    host: str = "127.0.0.1"
    
    # Templates
    auto_reload_templates: bool = True
    cache_templates: bool = False
    
    # Gráficos
    resolucao_grafico: int = 300  # DPI
    largura_grafico: int = 800
    altura_grafico: int = 600
    tema_grafico: str = "plotly"
    
    # Exportação
    formats_export: List[str] = field(default_factory=lambda: ["pdf", "png", "html"])
    qualidade_export: str = "alta"

# =============================================================================
# CONFIGURAÇÕES DE CÁLCULOS ESPECÍFICOS
# =============================================================================

@dataclass
class ConfigAletas:
    """Configurações específicas para cálculos de aletas"""
    
    # Condições de contorno
    condicoes_disponiveis: List[str] = field(default_factory=lambda: [
        "adiabatica", "conveccao", "infinita", "temp_especificada"
    ])
    condicao_padrao: str = "adiabatica"
    
    # Validação geométrica
    razao_aspecto_max: float = 1000.0  # L/t máximo
    razao_aspecto_min: float = 1.0     # L/t mínimo
    
    # Precisão de cálculo
    pontos_distribuicao_temp: int = 100
    usar_funcoes_bessel: bool = True

@dataclass
class ConfigConveccao:
    """Configurações para cálculos de convecção"""
    
    # Fluidos disponíveis
    fluidos_disponiveis: List[str] = field(default_factory=lambda: [
        "ar", "agua", "oleo", "vapor"
    ])
    fluido_padrao: str = "ar"
    
    # Correlações
    correlacao_padrao_natural: str = "rayleigh"
    correlacao_padrao_forcada: str = "dittus_boelter"
    
    # Ranges de validação
    re_min: float = 0.1
    re_max: float = 1e8
    pr_min: float = 0.1
    pr_max: float = 1000.0

# =============================================================================
# CLASSE DE CONFIGURAÇÃO PRINCIPAL
# =============================================================================

class ConfiguracaoSistema:
    """Configuração central do sistema"""
    
    def __init__(self):
        self.materiais = MATERIAIS_OTIMIZADOS
        self.validacao = LimitesValidacao()
        self.performance = ConfigPerformance()
        self.interface = ConfigInterface()
        self.aletas = ConfigAletas()
        self.conveccao = ConfigConveccao()
        
        # Carregar configurações do arquivo se existir
        self.carregar_configuracao()
    
    def carregar_configuracao(self, arquivo: str = "config.json") -> None:
        """Carrega configurações de arquivo JSON"""
        if os.path.exists(arquivo):
            try:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                    
                # Aplicar configurações carregadas
                for secao, valores in config_dict.items():
                    if hasattr(self, secao):
                        config_obj = getattr(self, secao)
                        for chave, valor in valores.items():
                            if hasattr(config_obj, chave):
                                setattr(config_obj, chave, valor)
                                
            except Exception as e:
                print(f"⚠️ Erro ao carregar configuração: {e}")
                print("🔄 Usando configurações padrão")
    
    def salvar_configuracao(self, arquivo: str = "config.json") -> None:
        """Salva configurações atuais em arquivo JSON"""
        config_dict = {}
        
        for attr_name in ['validacao', 'performance', 'interface', 'aletas', 'conveccao']:
            if hasattr(self, attr_name):
                attr_obj = getattr(self, attr_name)
                if hasattr(attr_obj, '__dict__'):
                    config_dict[attr_name] = attr_obj.__dict__
        
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuração salva em {arquivo}")
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
    
    def obter_material(self, nome: str) -> Optional[PropriedadesMaterial]:
        """Obtém propriedades de um material"""
        nome_lower = nome.lower().replace(" ", "_").replace("ç", "c").replace("ã", "a")
        return self.materiais.get(nome_lower)
    
    def validar_configuracao(self) -> List[str]:
        """Valida configurações atuais"""
        problemas = []
        
        # Validar limites físicos
        if self.validacao.temp_min >= self.validacao.temp_max:
            problemas.append("Temperatura mínima >= máxima")
            
        if self.validacao.h_min >= self.validacao.h_max:
            problemas.append("Coeficiente h mínimo >= máximo")
        
        # Validar performance
        if self.performance.cache_ttl_segundos <= 0:
            problemas.append("TTL do cache deve ser positivo")
            
        if self.performance.max_iteracoes <= 0:
            problemas.append("Máximo de iterações deve ser positivo")
        
        # Validar interface
        if self.interface.port < 1024 or self.interface.port > 65535:
            problemas.append("Porta deve estar entre 1024-65535")
        
        return problemas
    
    def aplicar_perfil_performance(self, perfil: str) -> None:
        """Aplica perfil de performance predefinido"""
        if perfil == "rapido":
            self.performance.cache_ttl_segundos = 7200  # 2 horas
            self.performance.precisao_numerica = 4
            self.performance.max_iteracoes = 500
            self.performance.usar_multiprocessing = True
            
        elif perfil == "balanceado":
            self.performance.cache_ttl_segundos = 3600  # 1 hora
            self.performance.precisao_numerica = 6
            self.performance.max_iteracoes = 1000
            self.performance.usar_multiprocessing = False
            
        elif perfil == "precisao":
            self.performance.cache_ttl_segundos = 1800  # 30 min
            self.performance.precisao_numerica = 8
            self.performance.max_iteracoes = 2000
            self.performance.tolerancia_convergencia = 1e-8
            
        print(f"✅ Perfil '{perfil}' aplicado")

# =============================================================================
# INSTÂNCIA GLOBAL DE CONFIGURAÇÃO
# =============================================================================

# Configuração global do sistema
config = ConfiguracaoSistema()

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def obter_limites_material(nome_material: str) -> Tuple[float, float]:
    """Obtém limites de condutividade térmica para um material"""
    material = config.obter_material(nome_material)
    if material:
        return material.k_min, material.k_max
    return 0.1, 1000.0  # Limites genéricos

def validar_parametro_fisico(valor: float, tipo: str, nome: str = "") -> Tuple[bool, List[str]]:
    """Validação rápida de parâmetro físico"""
    erros = []
    
    if tipo == "temperatura":
        if valor < config.validacao.temp_min:
            erros.append(f"{nome} abaixo do zero absoluto")
        elif valor > config.validacao.temp_max:
            erros.append(f"{nome} acima do limite físico")
            
    elif tipo == "dimensao":
        if valor <= 0:
            erros.append(f"{nome} deve ser positiva")
        elif valor < config.validacao.dimensao_min:
            erros.append(f"{nome} muito pequena")
        elif valor > config.validacao.dimensao_max:
            erros.append(f"{nome} muito grande")
            
    elif tipo == "coeficiente_h":
        if valor <= 0:
            erros.append(f"{nome} deve ser positivo")
        elif valor > config.validacao.h_max:
            erros.append(f"{nome} acima do limite físico")
    
    return len(erros) == 0, erros

def gerar_relatorio_configuracao() -> str:
    """Gera relatório completo da configuração atual"""
    relatorio = f"""
⚙️ RELATÓRIO DE CONFIGURAÇÃO DO SISTEMA
{'='*60}

🔧 PERFORMANCE:
   • Cache TTL: {config.performance.cache_ttl_segundos}s
   • Precisão numérica: {config.performance.precisao_numerica} dígitos
   • Máx iterações: {config.performance.max_iteracoes}
   • Multiprocessing: {'✅' if config.performance.usar_multiprocessing else '❌'}

🌡️ VALIDAÇÃO FÍSICA:
   • Temp. mín/máx: {config.validacao.temp_min}°C / {config.validacao.temp_max}°C
   • Dimensão mín/máx: {config.validacao.dimensao_min}m / {config.validacao.dimensao_max}m
   • Coef. h mín/máx: {config.validacao.h_min} / {config.validacao.h_max} W/m²·K

🌐 INTERFACE:
   • Porta: {config.interface.port}
   • Debug: {'✅' if config.interface.debug_mode else '❌'}
   • Resolução gráficos: {config.interface.resolucao_grafico} DPI

📊 MATERIAIS DISPONÍVEIS:
"""
    
    for nome, material in config.materiais.items():
        relatorio += f"   • {material.nome}: k={material.k} W/m·K (custo: {material.custo_relativo}/10)\n"
    
    # Validar configuração
    problemas = config.validar_configuracao()
    if problemas:
        relatorio += f"\n⚠️ PROBLEMAS DETECTADOS:\n"
        for problema in problemas:
            relatorio += f"   • {problema}\n"
    else:
        relatorio += f"\n✅ Configuração validada com sucesso!\n"
    
    return relatorio

if __name__ == "__main__":
    print(gerar_relatorio_configuracao())
    
    # Exemplo de uso
    print("\n🔄 Testando perfis de performance...")
    config.aplicar_perfil_performance("rapido")
    print(f"Precisão atual: {config.performance.precisao_numerica}")
    
    config.aplicar_perfil_performance("precisao")
    print(f"Precisão atual: {config.performance.precisao_numerica}")