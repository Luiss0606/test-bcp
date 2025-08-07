import { useState, useEffect } from 'react';
import { Modal } from './ui/modal';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  Calculator, 
  TrendingUp, 
  Clock, 
  DollarSign, 
  AlertTriangle,
  CheckCircle,
  FileText,
  BarChart3,
  Sparkles
} from 'lucide-react';

interface StrategyData {
  total_payoff_months: number;
  total_interest: number;
  total_payments: number;
  savings_vs_minimum: number;
  total_monthly_payment: number;
}

interface StrategyReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  strategy: 'minimum' | 'optimized' | 'consolidation';
  strategyData: StrategyData;
  customerId: string;
  formatCurrency: (amount: number) => string;
  isRecommended?: boolean;
  agentReport?: string;
}

export function StrategyReportModal({ 
  isOpen, 
  onClose, 
  strategy, 
  strategyData, 
  customerId,
  formatCurrency,
  isRecommended = false,
  agentReport
}: StrategyReportModalProps) {
  const [detailedReport, setDetailedReport] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const strategyConfig = {
    minimum: {
      title: 'Estrategia de Pago Mínimo',
      description: 'Análisis detallado del pago mínimo requerido',
      icon: Clock,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200'
    },
    optimized: {
      title: 'Plan Optimizado',
      description: 'Estrategia de pago acelerado y eficiente',
      icon: TrendingUp,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200'
    },
    consolidation: {
      title: 'Estrategia de Consolidación',
      description: 'Unificación de todas las deudas',
      icon: BarChart3,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200'
    }
  };

  const config = strategyConfig[strategy];
  const IconComponent = config.icon;

  // Use agent report if available, otherwise fetch from API
  useEffect(() => {
    if (isOpen) {
      if (agentReport) {
        // Use the pre-generated agent report
        setDetailedReport(agentReport);
        setIsLoading(false);
        setError('');
      } else if (customerId) {
        // Fallback to fetching from API
        fetchDetailedReport();
      }
    }
  }, [isOpen, customerId, strategy, agentReport]);

  const fetchDetailedReport = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/customers/${customerId}/scenarios/${strategy}`
      );
      
      if (response.ok) {
        const data = await response.json();
        // The detailed analysis should be in the response
        setDetailedReport(data.detailed_analysis || generateFallbackReport());
      } else {
        setError('No se pudo cargar el informe detallado');
        setDetailedReport(generateFallbackReport());
      }
    } catch (error) {
      setError('Error de conexión al cargar el informe');
      setDetailedReport(generateFallbackReport());
    } finally {
      setIsLoading(false);
    }
  };

  const generateFallbackReport = () => {
    const strategyNames = {
      minimum: 'pago mínimo',
      optimized: 'plan optimizado',
      consolidation: 'consolidación'
    };

    return `
INFORME DETALLADO - ${strategyNames[strategy].toUpperCase()}

RESUMEN FINANCIERO:
• Duración del plan: ${strategyData.total_payoff_months} meses
• Pago mensual: ${formatCurrency(strategyData.total_monthly_payment)}
• Total de intereses: ${formatCurrency(strategyData.total_interest)}
• Pago total: ${formatCurrency(strategyData.total_payments)}
${strategyData.savings_vs_minimum > 0 ? `• Ahorro vs mínimo: ${formatCurrency(strategyData.savings_vs_minimum)}` : ''}

ANÁLISIS:
${strategy === 'minimum' ? 
  'Esta estrategia implica pagar solo el mínimo requerido cada mes. Aunque ofrece pagos mensuales más bajos, resultará en un mayor costo total debido a los intereses acumulados durante más tiempo.' :
  strategy === 'optimized' ?
  'Esta estrategia busca optimizar sus pagos para reducir el tiempo de pago y los intereses totales. Requiere pagos mensuales más altos, pero ofrece ahorros significativos a largo plazo.' :
  'Esta estrategia consolida todas sus deudas en una sola, potencialmente con una tasa de interés más favorable. Simplifica la gestión de pagos y puede ofrecer ahorros en intereses.'
}

RECOMENDACIONES:
${strategy === 'minimum' ? 
  '• Considere esta opción solo si su flujo de efectivo es muy limitado\n• Evalúe la posibilidad de pagos adicionales cuando sea posible\n• Monitoree regularmente su capacidad de pago' :
  strategy === 'optimized' ?
  '• Asegúrese de que puede mantener los pagos más altos consistentemente\n• Esta opción ofrece el mejor balance entre ahorro y flexibilidad\n• Considere automatizar los pagos para evitar retrasos' :
  '• Verifique las condiciones del préstamo de consolidación\n• Compare las tasas de interés cuidadosamente\n• Considere el impacto en su score crediticio'
}
    `.trim();
  };

  const calculateProgress = () => {
    // Progress based on how much of the debt is paid vs total
    const totalDebt = strategyData.total_payments - strategyData.total_interest;
    return Math.round((totalDebt / strategyData.total_payments) * 100);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={config.title}
      size="xl"
    >
      <div className="p-6 space-y-6">
        {/* Header with strategy info */}
        <div className={cn("p-4 rounded-lg border-2", config.bgColor, config.borderColor)}>
          <div className="flex items-center space-x-3">
            <div className={cn("p-2 rounded-full bg-white shadow-sm")}>
              <IconComponent className={cn("w-6 h-6", config.color)} />
            </div>
            <div className="flex-1">
              <h3 className={cn("font-semibold text-lg", config.color)}>
                {config.title}
                {isRecommended && (
                  <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                    <Sparkles className="w-3 h-3 mr-1" />
                    RECOMENDADO
                  </span>
                )}
              </h3>
              <p className="text-sm text-muted-foreground">{config.description}</p>
            </div>
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4 text-center">
              <Clock className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
              <div className="text-2xl font-bold">{strategyData.total_payoff_months}</div>
              <div className="text-xs text-muted-foreground">meses</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center">
              <DollarSign className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
              <div className="text-lg font-bold">{formatCurrency(strategyData.total_monthly_payment)}</div>
              <div className="text-xs text-muted-foreground">pago mensual</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center">
              <Calculator className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
              <div className="text-lg font-bold">{formatCurrency(strategyData.total_interest)}</div>
              <div className="text-xs text-muted-foreground">intereses totales</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4 text-center">
              {strategyData.savings_vs_minimum > 0 ? (
                <>
                  <TrendingUp className="w-6 h-6 mx-auto mb-2 text-green-600" />
                  <div className="text-lg font-bold text-green-600">
                    {formatCurrency(strategyData.savings_vs_minimum)}
                  </div>
                  <div className="text-xs text-muted-foreground">ahorro vs mínimo</div>
                </>
              ) : (
                <>
                  <FileText className="w-6 h-6 mx-auto mb-2 text-muted-foreground" />
                  <div className="text-lg font-bold">{formatCurrency(strategyData.total_payments)}</div>
                  <div className="text-xs text-muted-foreground">pago total</div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Progress visualization */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Composición del Pago
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Capital</span>
                <span>{formatCurrency(strategyData.total_payments - strategyData.total_interest)}</span>
              </div>
              <Progress value={calculateProgress()} className="h-3" />
              <div className="flex justify-between text-sm">
                <span>Intereses</span>
                <span>{formatCurrency(strategyData.total_interest)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Detailed report */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center">
              <FileText className="w-5 h-5 mr-2" />
              Análisis Detallado
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                  <span>Cargando análisis detallado...</span>
                </div>
              </div>
            ) : error ? (
              <div className="flex items-center space-x-2 text-orange-600 bg-orange-50 p-3 rounded-lg">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-sm">{error}</span>
              </div>
            ) : (
              <div className="bg-muted/50 p-4 rounded-lg">
                <div className="prose prose-sm max-w-none text-sm leading-relaxed">
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({children}) => <h1 className="text-xl font-bold mb-4 text-primary">{children}</h1>,
                      h2: ({children}) => <h2 className="text-lg font-semibold mb-3 text-primary">{children}</h2>,
                      h3: ({children}) => <h3 className="text-base font-semibold mb-2 text-primary">{children}</h3>,
                      h4: ({children}) => <h4 className="text-sm font-semibold mb-2 text-primary">{children}</h4>,
                      p: ({children}) => <p className="mb-3 text-sm leading-relaxed">{children}</p>,
                      ul: ({children}) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
                      li: ({children}) => <li className="text-sm leading-relaxed">{children}</li>,
                      strong: ({children}) => <strong className="font-semibold text-primary">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      code: ({children}) => <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                      pre: ({children}) => <pre className="bg-muted p-3 rounded-lg overflow-x-auto text-xs">{children}</pre>,
                      blockquote: ({children}) => <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground">{children}</blockquote>,
                      table: ({children}) => <table className="w-full border-collapse border border-muted text-xs">{children}</table>,
                      th: ({children}) => <th className="border border-muted px-2 py-1 bg-muted font-semibold">{children}</th>,
                      td: ({children}) => <td className="border border-muted px-2 py-1">{children}</td>,
                    }}
                  >
                    {detailedReport}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action buttons */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
          {isRecommended && (
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <CheckCircle className="w-4 h-4 mr-2" />
              Seleccionar Esta Opción
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
