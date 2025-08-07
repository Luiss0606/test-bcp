import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface CustomerProfile {
  customer_profile: any;
  debts: Array<{
    debt_id: string;
    debt_type: string;
    balance: number;
    annual_rate_pct: number;
    minimum_payment: number;
    days_past_due: number;
    priority_score: number;
  }>;
}

interface AnalysisResult {
  customer_id: string;
  analysis_summary: any;
  scenarios: {
    minimum: any;
    optimized: any;
    consolidation: any;
  };
  ai_analysis: any;
}

function App() {
  const [customerId, setCustomerId] = useState<string>('');
  const [customerProfile, setCustomerProfile] = useState<CustomerProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>('');
  const [profileLoaded, setProfileLoaded] = useState(false);

  const loadCustomerProfile = async (clientId: string) => {
    setIsLoadingProfile(true);
    setError('');
    setAnalysisResult(null);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/customers/${clientId}/profile`);
      if (response.ok) {
        const data = await response.json();
        setCustomerProfile(data);
        setProfileLoaded(true);
      } else if (response.status === 404) {
        setError('No encontramos tu ID de cliente. Por favor verifica que sea correcto.');
        setCustomerProfile(null);
        setProfileLoaded(false);
      } else {
        setError('Error al cargar tu información. Inténtalo de nuevo.');
        setCustomerProfile(null);
        setProfileLoaded(false);
      }
    } catch (error) {
      setError('Error de conexión. Verifica tu conexión a internet.');
      setCustomerProfile(null);
      setProfileLoaded(false);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  const handleCustomerIdSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customerId.trim()) {
      loadCustomerProfile(customerId.trim());
    }
  };

  const handleAnalyze = async () => {
    if (!customerId) return;
    
    setIsAnalyzing(true);
    setError('');
    try {
      const response = await fetch(`http://localhost:8000/api/v1/customers/${customerId}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        setAnalysisResult(result);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error al generar tu análisis. Inténtalo de nuevo.');
      }
    } catch (error) {
      setError('Error de conexión. Verifica tu conexión a internet.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Tu Asistente de Reestructuración Financiera
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Ingresa tu ID de cliente para obtener un análisis personalizado de tus deudas
            y descubre las mejores opciones para optimizar tus pagos.
          </p>
        </div>

        <div className="max-w-4xl mx-auto">
          {/* Ingreso de ID de Cliente */}
          <Card className="mb-6 shadow-lg border-border bg-card">
            <CardHeader className="bg-primary text-primary-foreground rounded-t-lg">
              <CardTitle className="text-2xl">Accede a tu Análisis Financiero</CardTitle>
              <CardDescription className="text-primary-foreground/80">
                Ingresa tu ID de cliente para comenzar
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <form onSubmit={handleCustomerIdSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="customerId">Tu ID de Cliente</Label>
                  <Input
                    id="customerId"
                    type="text"
                    placeholder="Ej: CU-001"
                    value={customerId}
                    onChange={(e) => setCustomerId(e.target.value)}
                    className="text-lg"
                  />
                  <p className="text-sm text-muted-foreground">
                    Encuentra tu ID de cliente en tu estado de cuenta o documentos del banco.
                  </p>
                </div>
                <Button 
                  type="submit" 
                  disabled={!customerId.trim() || isLoadingProfile}
                  className="w-full"
                  size="lg"
                >
                  {isLoadingProfile ? 'Verificando...' : 'Verificar mi ID'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Tu Perfil Financiero */}
          {profileLoaded && customerProfile && (
            <Card className="mb-6 shadow-lg border-border bg-card">
              <CardHeader className="bg-secondary text-secondary-foreground rounded-t-lg">
                <CardTitle className="text-2xl">Tu Perfil Financiero</CardTitle>
                <CardDescription className="text-secondary-foreground/80">
                  Resumen de tu situación financiera actual
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <h3 className="font-semibold text-lg mb-2">Tu Información</h3>
                      <div className="space-y-2 text-sm">
                        <p><strong>ID de Cliente:</strong> {customerProfile.customer_profile.customer_id}</p>
                        <p><strong>Score Crediticio:</strong> {customerProfile.customer_profile.credit_score}</p>
                        <p><strong>Ingresos Mensuales:</strong> {formatCurrency(customerProfile.customer_profile.monthly_income)}</p>
                      </div>
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg mb-2">Resumen de tus Deudas</h3>
                      <div className="space-y-2 text-sm">
                        <p><strong>Total de Deudas:</strong> {customerProfile.debts.length}</p>
                        <p><strong>Balance Total:</strong> {formatCurrency(customerProfile.debts.reduce((sum, debt) => sum + debt.balance, 0))}</p>
                        <p><strong>Pago Mínimo Total:</strong> {formatCurrency(customerProfile.debts.reduce((sum, debt) => sum + debt.minimum_payment, 0))}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-lg mb-2">Detalle de tus Deudas</h3>
                    <div className="space-y-2">
                      {customerProfile.debts.map((debt) => (
                        <div key={debt.debt_id} className="flex justify-between items-center p-3 bg-muted rounded-lg">
                          <div className="flex-1">
                            <span className="font-medium capitalize">{debt.debt_type}</span>
                            <span className="text-muted-foreground ml-2">
                              Balance: {formatCurrency(debt.balance)} | 
                              Tasa: {debt.annual_rate_pct}% | 
                              Pago Mínimo: {formatCurrency(debt.minimum_payment)}
                              {debt.days_past_due > 0 && (
                                <span className="text-destructive ml-2">
                                  ({debt.days_past_due} días atrasado)
                                </span>
                              )}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Botón de Análisis */}
          {profileLoaded && customerProfile && (
            <div className="text-center mb-6">
              <Button 
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                size="lg"
                className="px-8 py-3 text-lg font-semibold shadow-lg transform transition hover:scale-105"
              >
                {isAnalyzing ? 'Generando tu Análisis...' : 'Generar mi Reporte Personalizado'}
              </Button>
              <p className="text-sm text-muted-foreground mt-2">
                Nuestro análisis con IA te mostrará las mejores opciones para optimizar tus pagos
              </p>
            </div>
          )}

          {/* Error */}
          {error && (
            <Card className="mb-6 border-destructive bg-destructive/10">
              <CardContent className="p-4">
                <p className="text-destructive">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Tu Reporte Personalizado */}
          {analysisResult && (
            <Card className="shadow-lg border-border bg-card">
              <CardHeader className="bg-accent text-accent-foreground rounded-t-lg">
                <CardTitle className="text-2xl">Tu Reporte Personalizado</CardTitle>
                <CardDescription className="text-accent-foreground/80">
                  Plan de reestructuración financiera diseñado específicamente para ti
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-6">
                  {/* Resumen de tu Situación */}
                  {analysisResult.analysis_summary && (
                    <div>
                      <h3 className="font-semibold text-lg mb-3">📊 Resumen de tu Situación</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div className="bg-primary/10 p-4 rounded-lg border border-primary/20">
                          <h4 className="font-medium text-primary">Tu Deuda Total</h4>
                          <p className="text-2xl font-bold text-primary">
                            {formatCurrency(analysisResult.analysis_summary.total_balance)}
                          </p>
                        </div>
                        <div className="bg-secondary/10 p-4 rounded-lg border border-secondary/20">
                          <h4 className="font-medium text-secondary">Dinero Disponible</h4>
                          <p className="text-2xl font-bold text-secondary">
                            {formatCurrency(analysisResult.analysis_summary.available_cashflow)}
                          </p>
                        </div>
                        <div className="bg-accent/10 p-4 rounded-lg border border-accent/20">
                          <h4 className="font-medium text-accent-foreground">Tasa Promedio</h4>
                          <p className="text-2xl font-bold text-accent-foreground">
                            {analysisResult.analysis_summary.weighted_avg_rate?.toFixed(2)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Recomendaciones Personalizadas */}
                  {analysisResult.ai_analysis && (
                    <div>
                      <h3 className="font-semibold text-lg mb-3">🤖 Tus Recomendaciones Personalizadas</h3>
                      <div className="bg-muted p-4 rounded-lg">
                        <pre className="whitespace-pre-wrap text-sm overflow-auto max-h-96">
                          {typeof analysisResult.ai_analysis === 'string' 
                            ? analysisResult.ai_analysis 
                            : JSON.stringify(analysisResult.ai_analysis, null, 2)
                          }
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Tus Opciones de Pago */}
                  {analysisResult.scenarios && (
                    <div>
                      <h3 className="font-semibold text-lg mb-3">📈 Tus Opciones de Pago</h3>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {Object.entries(analysisResult.scenarios).map(([scenario, data]: [string, any]) => {
                          const scenarioNames = {
                            minimum: 'Pago Mínimo',
                            optimized: 'Plan Optimizado',
                            consolidation: 'Consolidación'
                          };
                          return (
                            <div key={scenario} className="border border-border rounded-lg p-4 bg-card">
                              <h4 className="font-medium mb-2">{scenarioNames[scenario as keyof typeof scenarioNames]}</h4>
                              <div className="text-sm space-y-1">
                                <p><strong>Tiempo:</strong> {data.total_months} meses</p>
                                <p><strong>Interés Total:</strong> {formatCurrency(data.total_interest)}</p>
                                <p><strong>Pago Total:</strong> {formatCurrency(data.total_payment)}</p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Información Adicional */}
          {!profileLoaded && !error && (
            <Card className="shadow-lg border-border bg-card">
              <CardContent className="p-6 text-center">
                <h3 className="font-semibold text-lg mb-3">¿Cómo funciona?</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="space-y-2">
                    <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center mx-auto">
                      <span className="text-primary font-bold">1</span>
                    </div>
                    <h4 className="font-medium">Ingresa tu ID</h4>
                    <p className="text-sm text-muted-foreground">
                      Proporciona tu ID de cliente para acceder a tu información
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="w-12 h-12 bg-secondary/20 rounded-full flex items-center justify-center mx-auto">
                      <span className="text-secondary font-bold">2</span>
                    </div>
                    <h4 className="font-medium">Revisamos tus datos</h4>
                    <p className="text-sm text-muted-foreground">
                      Analizamos tu situación financiera actual y tus deudas
                    </p>
                  </div>
                  <div className="space-y-2">
                    <div className="w-12 h-12 bg-accent/20 rounded-full flex items-center justify-center mx-auto">
                      <span className="text-accent-foreground font-bold">3</span>
                    </div>
                    <h4 className="font-medium">Obtienes tu plan</h4>
                    <p className="text-sm text-muted-foreground">
                      Recibes recomendaciones personalizadas para optimizar tus pagos
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;