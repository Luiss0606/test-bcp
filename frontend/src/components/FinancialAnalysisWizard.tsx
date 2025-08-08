import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Stepper } from "@/components/ui/stepper";
import { Progress } from "@/components/ui/progress";
import { StrategyReportModal } from "./StrategyReportModal";
import { PaymentComparisonChart } from "./PaymentComparisonChart";
import { cn } from '@/lib/utils';
import { ChevronRight, ChevronLeft, CheckCircle, AlertCircle, TrendingUp, Calculator, FileText, Sparkles, Eye, Crown, Download } from 'lucide-react';
import jsPDF from 'jspdf';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { apiFetch } from '@/lib/api';

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
  individual_analyses?: {
    minimum_analysis?: string;
    optimized_analysis?: string;
    consolidation_analysis?: string;
  };
  consolidated_report?: string;
  recommendations?: string[];
  summary_metrics?: any;
}

const steps = [
  {
    id: 'welcome',
    title: 'Bienvenida',
    description: 'Ingresa tu ID'
  },
  {
    id: 'profile',
    title: 'Tu Perfil',
    description: 'Verificación'
  },
  {
    id: 'analysis',
    title: 'Análisis',
    description: 'Procesando'
  },
  {
    id: 'results',
    title: 'Resultados',
    description: 'Tu plan'
  }
];

export function FinancialAnalysisWizard() {
  const [currentStep, setCurrentStep] = useState(1);
  const [customerId, setCustomerId] = useState<string>('');
  const [customerProfile, setCustomerProfile] = useState<CustomerProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);

  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>('');
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [selectedStrategy, setSelectedStrategy] = useState<'minimum' | 'optimized' | 'consolidation' | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN'
    }).format(amount);
  };

  const loadCustomerProfile = async (clientId: string) => {
    setIsLoadingProfile(true);
    setError('');
    try {
      const response = await apiFetch(`/api/v1/customers/${clientId}/profile`);
      if (response.ok) {
        const data = await response.json();
        // Adapt backend response to UI contract
        const mapBackendProfileToUI = (payload: any): CustomerProfile => {
          // New backend returns a flat array in payload.debts
          let debts: any[] = [];
          if (Array.isArray(payload?.debts)) {
            debts = payload.debts.map((d: any) => ({
              debt_id: d.debt_id ?? d.id,
              debt_type: d.debt_type ?? (d.product_type ? 'loan' : 'card'),
              balance: Number(d.balance ?? 0),
              annual_rate_pct: Number(d.annual_rate_pct ?? d.rate ?? 0),
              minimum_payment: Number(d.minimum_payment ?? 0),
              days_past_due: Number(d.days_past_due ?? 0),
              priority_score: typeof d.priority_score === 'number' ? d.priority_score : 0,
            }));
          } else {
            // Backward compatibility: split objects {loans:[], cards:[]}
            const loans = payload?.debts?.loans ?? [];
            const cards = payload?.debts?.cards ?? [];
            debts = [
              ...loans.map((l: any) => ({
                debt_id: l.id,
                debt_type: 'loan',
                balance: Number(l.balance ?? 0),
                annual_rate_pct: Number(l.annual_rate_pct ?? l.rate ?? 0),
                minimum_payment: Number(l.minimum_payment ?? 0),
                days_past_due: Number(l.days_past_due ?? 0),
                priority_score: typeof l.priority_score === 'number' ? l.priority_score : 0,
              })),
              ...cards.map((c: any) => ({
                debt_id: c.id,
                debt_type: 'card',
                balance: Number(c.balance ?? 0),
                annual_rate_pct: Number(c.annual_rate_pct ?? c.rate ?? 0),
                minimum_payment: Number(c.minimum_payment ?? 0),
                days_past_due: Number(c.days_past_due ?? 0),
                priority_score: typeof c.priority_score === 'number' ? c.priority_score : 0,
              })),
            ];
          }

          return {
            customer_profile: {
              customer_id: payload?.customer_id ?? payload?.profile?.customer_id,
              credit_score: payload?.profile?.credit_score,
              monthly_income: payload?.profile?.monthly_income,
              available_cashflow: payload?.profile?.available_cashflow,
              total_debt_balance: payload?.profile?.total_debt_balance,
              total_minimum_payment: payload?.profile?.total_minimum_payment,
              ...payload?.profile,
            },
            debts,
          } as CustomerProfile;
        };

        setCustomerProfile(mapBackendProfileToUI(data));
        // Auto-advance to profile step
        setTimeout(() => {
          setCurrentStep(2);
        }, 800);
      } else if (response.status === 404) {
        setError('No encontramos tu ID de cliente. Por favor verifica que sea correcto.');
      } else {
        setError('Error al cargar tu información. Inténtalo de nuevo.');
      }
    } catch (error) {
      setError('Error de conexión. Verifica tu conexión a internet.');
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

    setCurrentStep(3);
    setError('');
    setAnalysisProgress(0);

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setAnalysisProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + Math.random() * 3;
      });
    }, 500);

    try {
      const response = await apiFetch(`/api/v1/customers/${customerId}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const result = await response.json();
        // Normalize analysis result to expected UI contract
        const normalized = {
          customer_id: result.customer_id,
          analysis_summary: result.summary_metrics ? {
            total_balance: result.customer_profile?.total_debt_balance ?? 0,
            available_cashflow: result.customer_profile?.available_cashflow ?? 0,
            weighted_avg_rate: result.customer_profile?.average_interest_rate ?? 0,
          } : undefined,
          scenarios: result.scenarios,
          ai_analysis: result.consolidated_report,
          individual_analyses: result.individual_analyses,
          consolidated_report: result.consolidated_report,
          recommendations: result.recommendations,
          summary_metrics: result.summary_metrics,
        } as AnalysisResult;
        setAnalysisResult(normalized);
        setAnalysisProgress(100);
        // Auto-advance to results
        setTimeout(() => {
          setCurrentStep(4);
        }, 1000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Error al generar tu análisis. Inténtalo de nuevo.');
        setCurrentStep(2); // Go back to profile step
      }
    } catch (error) {
      setError('Error de conexión. Verifica tu conexión a internet.');
      setCurrentStep(2); // Go back to profile step
    } finally {
      clearInterval(progressInterval);
    }
  };

  const goToStep = (step: number) => {
    if (step === 1) {
      setCurrentStep(1);
      setCustomerProfile(null);
      setAnalysisResult(null);
      setError('');
    } else if (step === 2 && customerProfile) {
      setCurrentStep(2);
    }
  };

  const handleStrategyClick = (strategy: 'minimum' | 'optimized' | 'consolidation') => {
    setSelectedStrategy(strategy);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedStrategy(null);
  };

  const generatePDF = () => {
    if (!analysisResult) return;

    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    // Helpers
    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const marginLeft = 15;
    const marginRight = 15;
    const contentWidth = pageWidth - marginLeft - marginRight;
    let cursorY = 20;

    const addHeader = () => {
      // Header band
      pdf.setFillColor(240, 248, 255); // aliceblue
      pdf.rect(0, 0, pageWidth, 22, 'F');
      pdf.setTextColor(33, 37, 41);
      pdf.setFontSize(16);
      pdf.text('Informe de Reestructuración Financiera', marginLeft, 14);
      pdf.setFontSize(10);
      pdf.setTextColor(100);
      pdf.text(`Cliente: ${customerId}`, marginLeft, 20);
      pdf.text(`Fecha: ${new Date().toLocaleDateString('es-MX')}`, pageWidth - marginRight - 45, 20);
      cursorY = 28;
    };

    const sectionTitle = (title: string) => {
      if (cursorY + 10 > pageHeight - 15) newPage();
      pdf.setDrawColor(230);
      pdf.line(marginLeft, cursorY, pageWidth - marginRight, cursorY);
      cursorY += 6;
      pdf.setTextColor(25, 118, 210); // primary blue
      pdf.setFontSize(13);
      pdf.text(title, marginLeft, cursorY);
      pdf.setTextColor(33, 37, 41);
      cursorY += 4;
    };

    const kvRow = (label: string, value: string, yPad = 6) => {
      if (cursorY + yPad > pageHeight - 15) newPage();
      pdf.setFontSize(10);
      pdf.setTextColor(120);
      pdf.text(label, marginLeft, cursorY);
      pdf.setTextColor(33, 37, 41);
      pdf.text(value, marginLeft + 60, cursorY);
      cursorY += yPad;
    };

    const twoColBox = (left: { label: string; value: string }, right: { label: string; value: string }) => {
      if (cursorY + 18 > pageHeight - 15) newPage();
      const boxY = cursorY;
      pdf.setDrawColor(230);
      pdf.setFillColor(249, 250, 251); // light gray
      pdf.roundedRect(marginLeft, boxY, contentWidth, 16, 2, 2, 'FD');
      pdf.setFontSize(11);
      pdf.setTextColor(120);
      pdf.text(left.label, marginLeft + 6, boxY + 6);
      pdf.setTextColor(33, 37, 41);
      pdf.text(left.value, marginLeft + 6, boxY + 12);
      pdf.setTextColor(120);
      pdf.text(right.label, marginLeft + contentWidth / 2 + 6, boxY + 6);
      pdf.setTextColor(33, 37, 41);
      pdf.text(right.value, marginLeft + contentWidth / 2 + 6, boxY + 12);
      cursorY += 20;
    };

    const multiText = (text: string) => {
      const lines = pdf.splitTextToSize(text, contentWidth);
      const lineHeight = 5;
      lines.forEach((line: string) => {
        if (cursorY + lineHeight > pageHeight - 15) newPage();
        pdf.text(line, marginLeft, cursorY);
        cursorY += lineHeight;
      });
    };

    const newPage = () => {
      pdf.addPage();
      addHeader();
    };

    // Header
    addHeader();

    // Resumen ejecutivo
    sectionTitle('Resumen Ejecutivo');
    // summary_metrics disponible si backend lo envía; no usado directamente aquí
    const prof = (analysisResult as any)?.analysis_summary;
    twoColBox(
      { label: 'Deuda Total', value: formatCurrency(prof?.total_balance ?? 0) },
      { label: 'Flujo Disponible', value: formatCurrency(prof?.available_cashflow ?? 0) }
    );
    kvRow('Tasa promedio', `${Number(prof?.weighted_avg_rate ?? 0).toFixed(2)} %`);
    cursorY += 2;

    // Escenarios
    sectionTitle('Comparativa de Escenarios');
    const scenarios: any = analysisResult.scenarios || {};
    const row = (name: string, data: any) => {
      if (!data) return;
      if (cursorY + 14 > pageHeight - 15) newPage();
      pdf.setFillColor('#f5f5f5');
      pdf.roundedRect(marginLeft, cursorY - 5, contentWidth, 12, 2, 2, 'F');
      pdf.setFontSize(11);
      pdf.text(name, marginLeft + 4, cursorY + 2);
      pdf.setFontSize(10);
      const colsX = [marginLeft + 60, marginLeft + 105, marginLeft + 150];
      pdf.text(`Meses: ${data.total_payoff_months ?? 0}`, colsX[0], cursorY + 2);
      pdf.text(`Interés: ${formatCurrency(data.total_interest ?? 0)}`, colsX[1], cursorY + 2);
      pdf.text(`Ahorro: ${formatCurrency(data.savings_vs_minimum ?? 0)}`, colsX[2], cursorY + 2);
      cursorY += 14;
    };
    row('Pago Mínimo', scenarios.minimum);
    row('Plan Optimizado', scenarios.optimized);
    row('Consolidación', scenarios.consolidation);

    // Informe consolidado (IA)
    sectionTitle('Informe Detallado');
    const report = analysisResult.consolidated_report || analysisResult.ai_analysis || 'No hay informe disponible';
    multiText(report);

    // Recomendaciones
    if (analysisResult.recommendations && analysisResult.recommendations.length) {
      sectionTitle('Recomendaciones Clave');
      analysisResult.recommendations.forEach((r) => multiText(`• ${r}`));
    }

    // Footer with page number
    const pageCount = (pdf as any).internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i);
      pdf.setFontSize(9);
      pdf.setTextColor(150);
      pdf.text(`Página ${i} de ${pageCount}`, (pageWidth / 2) - 12, pageHeight - 8);
    }

    pdf.save(`informe-financiero-${customerId}-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-8 animate-in slide-in-from-right-5 duration-500">
            <div className="text-center space-y-4">
              <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                <Sparkles className="w-10 h-10 text-primary" />
              </div>
              <h2 className="text-3xl font-bold text-foreground">
                Bienvenido a tu Asistente Financiero
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Ingresa tu ID de cliente para obtener un análisis personalizado de tus deudas
                y descubrir las mejores opciones para optimizar tus pagos.
              </p>
            </div>

            <Card className="max-w-md mx-auto shadow-xl border-border bg-card">
              <CardHeader className="text-center">
                <CardTitle className="text-xl">Accede a tu Análisis</CardTitle>
                <CardDescription>
                  Ingresa tu ID de cliente para comenzar
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
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
                      Encuentra tu ID en tu estado de cuenta o documentos del banco.
                    </p>
                  </div>
                  <Button
                    type="submit"
                    disabled={!customerId.trim() || isLoadingProfile}
                    className="w-full"
                    size="lg"
                  >
                    {isLoadingProfile ? (
                      <>
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
                        Verificando...
                      </>
                    ) : (
                      <>
                        Verificar mi ID
                        <ChevronRight className="w-4 h-4 ml-2" />
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* How it works section */}
            <div className="max-w-4xl mx-auto">
              <h3 className="text-xl font-semibold text-center mb-6">¿Cómo funciona?</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center mx-auto">
                    <span className="text-primary font-bold">1</span>
                  </div>
                  <h4 className="font-medium">Ingresa tu ID</h4>
                  <p className="text-sm text-muted-foreground">
                    Proporciona tu ID de cliente para acceder a tu información
                  </p>
                </div>
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 bg-secondary/20 rounded-full flex items-center justify-center mx-auto">
                    <span className="text-secondary font-bold">2</span>
                  </div>
                  <h4 className="font-medium">Revisamos tus datos</h4>
                  <p className="text-sm text-muted-foreground">
                    Analizamos tu situación financiera actual y tus deudas
                  </p>
                </div>
                <div className="text-center space-y-3">
                  <div className="w-12 h-12 bg-accent/20 rounded-full flex items-center justify-center mx-auto">
                    <span className="text-accent-foreground font-bold">3</span>
                  </div>
                  <h4 className="font-medium">Obtienes tu plan</h4>
                  <p className="text-sm text-muted-foreground">
                    Recibes recomendaciones personalizadas para optimizar tus pagos
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 2:
        return customerProfile ? (
          <div className="space-y-8 animate-in slide-in-from-right-5 duration-500">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-foreground">
                ¡Perfecto! Encontramos tu información
              </h2>
              <p className="text-muted-foreground">
                Aquí tienes un resumen de tu situación financiera actual
              </p>
            </div>

            <Card className="max-w-4xl mx-auto shadow-xl">
              <CardHeader className="bg-secondary/10">
                <CardTitle className="text-xl flex items-center">
                  <FileText className="w-5 h-5 mr-2" />
                  Tu Perfil Financiero
                </CardTitle>
                <CardDescription>
                  Resumen de tu situación financiera actual
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h3 className="font-semibold text-lg mb-3">Tu Información</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">ID de Cliente:</span>
                        <span className="font-medium">{customerProfile.customer_profile.customer_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Score Crediticio:</span>
                        <span className="font-medium">{customerProfile.customer_profile.credit_score}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Ingresos Mensuales:</span>
                        <span className="font-medium">{formatCurrency(customerProfile.customer_profile.monthly_income)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-semibold text-lg mb-3">Resumen de tus Deudas</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total de Deudas:</span>
                        <span className="font-medium">{customerProfile.debts.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Balance Total:</span>
                        <span className="font-medium text-lg">{formatCurrency(customerProfile.debts.reduce((sum, debt) => sum + debt.balance, 0))}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Pago Mínimo Total:</span>
                        <span className="font-medium">{formatCurrency(customerProfile.debts.reduce((sum, debt) => sum + debt.minimum_payment, 0))}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="font-semibold text-lg">Detalle de tus Deudas</h3>
                  <div className="grid gap-3">
                    {customerProfile.debts.map((debt) => (
                      <div key={debt.debt_id} className="p-4 bg-muted/50 rounded-lg border">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <span className="font-medium capitalize text-lg">{debt.debt_type}</span>
                            <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                              <div>
                                <span className="text-muted-foreground">Balance:</span>
                                <div className="font-medium">{formatCurrency(debt.balance)}</div>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Tasa:</span>
                                <div className="font-medium">{debt.annual_rate_pct}%</div>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Pago Mínimo:</span>
                                <div className="font-medium">{formatCurrency(debt.minimum_payment)}</div>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Estado:</span>
                                <div className={cn("font-medium", {
                                  "text-green-600": debt.days_past_due === 0,
                                  "text-red-600": debt.days_past_due > 0
                                })}>
                                  {debt.days_past_due === 0 ? 'Al día' : `${debt.days_past_due} días atrasado`}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex justify-center pt-4">
                  <Button
                    onClick={handleAnalyze}
                    size="lg"
                    className="px-8 py-3 text-lg font-semibold shadow-lg"
                  >
                    <Calculator className="w-5 h-5 mr-2" />
                    Generar mi Análisis Personalizado
                    <ChevronRight className="w-5 h-5 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : null;

      case 3:
        return (
          <div className="space-y-8 animate-in slide-in-from-right-5 duration-500">
            <div className="text-center space-y-6">
              <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
                <TrendingUp className="w-10 h-10 text-primary animate-pulse" />
              </div>
              <h2 className="text-3xl font-bold text-foreground">
                Generando tu Análisis Personalizado
              </h2>
              <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                Nuestro sistema de inteligencia artificial está analizando tu situación financiera
                para crear el mejor plan de reestructuración para ti.
              </p>
            </div>

            <Card className="max-w-2xl mx-auto shadow-xl">
              <CardContent className="p-8 space-y-6">
                <Progress value={analysisProgress} showPercentage />

                <div className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <div className={cn("w-3 h-3 rounded-full", analysisProgress > 20 ? "bg-green-500" : "bg-muted animate-pulse")} />
                    <span className={cn("text-sm", analysisProgress > 20 ? "text-foreground" : "text-muted-foreground")}>
                      Analizando tus deudas actuales...
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className={cn("w-3 h-3 rounded-full", analysisProgress > 40 ? "bg-green-500" : "bg-muted animate-pulse")} />
                    <span className={cn("text-sm", analysisProgress > 40 ? "text-foreground" : "text-muted-foreground")}>
                      Calculando escenarios de pago...
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className={cn("w-3 h-3 rounded-full", analysisProgress > 60 ? "bg-green-500" : "bg-muted animate-pulse")} />
                    <span className={cn("text-sm", analysisProgress > 60 ? "text-foreground" : "text-muted-foreground")}>
                      Evaluando opciones de consolidación...
                    </span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className={cn("w-3 h-3 rounded-full", analysisProgress > 80 ? "bg-green-500" : "bg-muted animate-pulse")} />
                    <span className={cn("text-sm", analysisProgress > 80 ? "text-foreground" : "text-muted-foreground")}>
                      Generando recomendaciones personalizadas...
                    </span>
                  </div>
                </div>

                <div className="text-center pt-4">
                  <p className="text-sm text-muted-foreground">
                    Este proceso puede tomar unos momentos...
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 4:
        return analysisResult ? (
          <div className="space-y-8 animate-in slide-in-from-right-5 duration-500">
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h2 className="text-3xl font-bold text-foreground">
                ¡Tu Plan Personalizado está Listo!
              </h2>
            </div>

            <div className="max-w-6xl mx-auto space-y-6">

              {/* Master Report Section with Download */}
              <Card className="shadow-xl">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="flex items-center text-xl">
                        <Crown className="w-6 h-6 mr-2 text-primary" />
                        Informe Integral de Reestructuración
                      </CardTitle>
                      <CardDescription>
                        Análisis completo generado por el Director de Estrategia Financiera
                      </CardDescription>
                    </div>
                    <Button
                      onClick={generatePDF}
                      className="bg-primary hover:bg-primary/90"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Descargar PDF
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-6">
                  <div className="bg-muted/30 rounded-lg p-6 max-h-[400px] overflow-y-auto">
                    <div className="prose prose-sm max-w-none text-sm leading-relaxed">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({ children }) => <h1 className="text-xl font-bold mb-4 text-primary">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-lg font-semibold mb-3 text-primary">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-base font-semibold mb-2 text-primary">{children}</h3>,
                          h4: ({ children }) => <h4 className="text-sm font-semibold mb-2 text-primary">{children}</h4>,
                          p: ({ children }) => <p className="mb-3 text-sm leading-relaxed">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
                          li: ({ children }) => <li className="text-sm leading-relaxed">{children}</li>,
                          strong: ({ children }) => <strong className="font-semibold text-primary">{children}</strong>,
                          em: ({ children }) => <em className="italic">{children}</em>,
                          code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                          pre: ({ children }) => <pre className="bg-muted p-3 rounded-lg overflow-x-auto text-xs">{children}</pre>,
                          blockquote: ({ children }) => <blockquote className="border-l-4 border-primary pl-4 italic text-muted-foreground">{children}</blockquote>,
                          table: ({ children }) => <table className="w-full border-collapse border border-muted text-xs">{children}</table>,
                          th: ({ children }) => <th className="border border-muted px-2 py-1 bg-muted font-semibold">{children}</th>,
                          td: ({ children }) => <td className="border border-muted px-2 py-1">{children}</td>,
                        }}
                      >
                        {analysisResult.consolidated_report ||
                          analysisResult.ai_analysis ||
                          'Generando informe integral...'}
                      </ReactMarkdown>
                    </div>
                  </div>

                  {/* Recommendations Section */}
                  {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                    <div className="mt-6 p-4 bg-primary/5 rounded-lg border border-primary/20">
                      <h4 className="font-semibold text-primary mb-3 flex items-center gap-2">
                        <Sparkles className="w-4 h-4" />
                        Recomendaciones Clave
                      </h4>
                      <ul className="space-y-2">
                        {analysisResult.recommendations.map((rec, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
                            <span className="text-sm">{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Scenarios */}
              {analysisResult.scenarios && (
                <Card className="shadow-xl">
                  <CardHeader>
                    <CardTitle className="flex items-center text-xl">
                      <Calculator className="w-6 h-6 mr-2 text-primary" />
                      Tus Opciones de Pago
                    </CardTitle>
                    <CardDescription>
                      Compara diferentes estrategias para optimizar tus pagos
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {(() => {
                        // Find the best scenario based on savings_vs_minimum
                        let bestScenario = '';
                        let maxSavings = 0;

                        Object.entries(analysisResult.scenarios).forEach(([scenario, data]: [string, any]) => {
                          const savings = data.savings_vs_minimum || 0;
                          if (savings > maxSavings) {
                            maxSavings = savings;
                            bestScenario = scenario;
                          }
                        });

                        return Object.entries(analysisResult.scenarios).map(([scenario, data]: [string, any]) => {
                          const isRecommended = scenario === bestScenario && maxSavings > 0;
                          const savings = data.savings_vs_minimum || 0;

                          const scenarioConfig = {
                            minimum: {
                              name: 'Pago Mínimo',
                              description: 'Pagando solo el mínimo requerido',
                              color: isRecommended ? 'border-emerald-400 bg-emerald-50' : 'border-orange-200 bg-orange-50',
                              textColor: isRecommended ? 'text-emerald-700' : 'text-orange-700'
                            },
                            optimized: {
                              name: 'Plan Optimizado',
                              description: 'Estrategia de pago acelerado',
                              color: isRecommended ? 'border-emerald-400 bg-emerald-50' : 'border-blue-200 bg-blue-50',
                              textColor: isRecommended ? 'text-emerald-700' : 'text-blue-700'
                            },
                            consolidation: {
                              name: 'Consolidación',
                              description: 'Unificando todas tus deudas',
                              color: isRecommended ? 'border-emerald-400 bg-emerald-50' : 'border-green-200 bg-green-50',
                              textColor: isRecommended ? 'text-emerald-700' : 'text-green-700'
                            }
                          };

                          const config = scenarioConfig[scenario as keyof typeof scenarioConfig];

                          return (
                            <Card key={scenario} className={cn(
                              "border-2 relative transition-all duration-300 group cursor-pointer hover:shadow-lg",
                              config.color,
                              isRecommended && "ring-2 ring-emerald-300 shadow-lg recommended-card"
                            )}>
                              {isRecommended && (
                                <div className="absolute -top-3 left-1/2 recommended-badge">
                                  <div className="bg-gradient-to-r from-emerald-500 to-green-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center space-x-1 shadow-lg">
                                    <CheckCircle className="w-3 h-3" />
                                    <span>RECOMENDADO</span>
                                  </div>
                                </div>
                              )}

                              <CardHeader className="pb-3">
                                <CardTitle className={cn("text-lg flex items-center justify-between", config.textColor)}>
                                  {config.name}
                                  {isRecommended && (
                                    <div className="flex items-center text-emerald-600">
                                      <Sparkles className="w-4 h-4" />
                                    </div>
                                  )}
                                </CardTitle>
                                <CardDescription className="text-sm">
                                  {config.description}
                                </CardDescription>
                              </CardHeader>

                              <CardContent className="space-y-3">
                                <div className="space-y-2">
                                  <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">Tiempo:</span>
                                    <span className="font-medium">{data.total_payoff_months} meses</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-sm text-muted-foreground">Interés Total:</span>
                                    <span className="font-medium">{formatCurrency(data.total_interest)}</span>
                                  </div>
                                  {savings > 0 && (
                                    <div className="flex justify-between">
                                      <span className="text-sm text-muted-foreground">Ahorro vs Mínimo:</span>
                                      <span className="font-medium text-emerald-600">
                                        {formatCurrency(savings)}
                                      </span>
                                    </div>
                                  )}
                                  <div className="flex justify-between border-t pt-2">
                                    <span className="text-sm font-medium">Pago Total:</span>
                                    <span className="font-bold text-lg">{formatCurrency(data.total_payments)}</span>
                                  </div>
                                </div>

                                {isRecommended && (
                                  <div className="mt-4 p-3 bg-emerald-100 rounded-lg border border-emerald-200">
                                    <div className="flex items-center space-x-2">
                                      <TrendingUp className="w-4 h-4 text-emerald-600" />
                                      <span className="text-sm font-medium text-emerald-700">
                                        Mejor Opción Financiera
                                      </span>
                                    </div>
                                    <p className="text-xs text-emerald-600 mt-1">
                                      Esta opción te permite ahorrar más dinero en intereses
                                    </p>
                                  </div>
                                )}

                                {/* View Details Button */}
                                <div className="pt-3 border-t">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="w-full group-hover:bg-primary group-hover:text-primary-foreground transition-colors"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleStrategyClick(scenario as 'minimum' | 'optimized' | 'consolidation');
                                    }}
                                  >
                                    <Eye className="w-4 h-4 mr-2" />
                                    Ver Planificación Completa
                                  </Button>
                                </div>
                              </CardContent>
                            </Card>
                          );
                        });
                      })()}
                    </div>

                    {(() => {
                      // Show recommendation summary
                      let bestScenario = '';
                      let maxSavings = 0;

                      Object.entries(analysisResult.scenarios).forEach(([scenario, data]: [string, any]) => {
                        const savings = data.savings_vs_minimum || 0;
                        if (savings > maxSavings) {
                          maxSavings = savings;
                          bestScenario = scenario;
                        }
                      });

                      if (bestScenario && maxSavings > 0) {
                        const scenarioNames = {
                          minimum: 'Pago Mínimo',
                          optimized: 'Plan Optimizado',
                          consolidation: 'Consolidación'
                        };

                        return (
                          <div className="mt-8 p-6 bg-gradient-to-r from-emerald-50 via-green-50 to-emerald-50 rounded-xl border-2 border-emerald-200 shadow-lg">
                            <div className="flex items-start space-x-4">
                              <div className="flex-shrink-0">
                                <div className="w-12 h-12 bg-emerald-500 rounded-full flex items-center justify-center shadow-md">
                                  <CheckCircle className="w-7 h-7 text-white" />
                                </div>
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-2">
                                  <h4 className="text-xl font-bold text-emerald-800">
                                    💡 Nuestra Recomendación
                                  </h4>
                                  <Sparkles className="w-5 h-5 text-emerald-600" />
                                </div>
                                <div className="bg-white p-4 rounded-lg shadow-sm border border-emerald-100">
                                  <p className="text-emerald-700 leading-relaxed">
                                    <strong className="text-lg text-emerald-800">
                                      {scenarioNames[bestScenario as keyof typeof scenarioNames]}
                                    </strong> es tu mejor opción financiera.
                                  </p>
                                  <div className="mt-3 flex items-center space-x-2">
                                    <TrendingUp className="w-5 h-5 text-emerald-600" />
                                    <p className="text-sm text-emerald-600">
                                      <strong>Ahorro estimado: {formatCurrency(maxSavings)}</strong> en intereses comparado con pagar solo el mínimo.
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    })()}
                  </CardContent>
                </Card>
              )}

              {/* Payment Comparison Chart */}
              {analysisResult.scenarios && (
                <PaymentComparisonChart
                  scenarios={analysisResult.scenarios}
                  formatCurrency={formatCurrency}
                />
              )}

              <div className="flex justify-center pt-6">
                <Button
                  onClick={() => goToStep(1)}
                  variant="outline"
                  size="lg"
                  className="px-8"
                >
                  <ChevronLeft className="w-5 h-5 mr-2" />
                  Realizar Nuevo Análisis
                </Button>
              </div>
            </div>
          </div>
        ) : null;

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Asistente de Reestructuración Financiera
          </h1>
          <p className="text-muted-foreground">
            Tu camino hacia una mejor salud financiera
          </p>
        </div>

        {/* Stepper */}
        <div className="max-w-4xl mx-auto mb-8">
          <Stepper steps={steps} currentStep={currentStep} />
        </div>

        {/* Error Display */}
        {error && (
          <Card className="max-w-2xl mx-auto mb-6 border-destructive bg-destructive/10">
            <CardContent className="p-4 flex items-center space-x-3">
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0" />
              <p className="text-destructive">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Step Content */}
        <div className="max-w-6xl mx-auto">
          {renderStepContent()}
        </div>

        {/* Strategy Report Modal */}
        {selectedStrategy && analysisResult && (
          <StrategyReportModal
            isOpen={isModalOpen}
            onClose={closeModal}
            strategy={selectedStrategy}
            strategyData={analysisResult.scenarios[selectedStrategy]}
            customerId={customerId}
            formatCurrency={formatCurrency}
            agentReport={(() => {
              // Get the corresponding agent report
              if (analysisResult.individual_analyses) {
                const reportMap = {
                  'minimum': analysisResult.individual_analyses.minimum_analysis,
                  'optimized': analysisResult.individual_analyses.optimized_analysis,
                  'consolidation': analysisResult.individual_analyses.consolidation_analysis
                };
                return reportMap[selectedStrategy];
              }
              return undefined;
            })()}
            isRecommended={(() => {
              // Determine if this strategy is recommended
              let bestScenario = '';
              let maxSavings = 0;

              Object.entries(analysisResult.scenarios).forEach(([scenario, data]: [string, any]) => {
                const savings = data.savings_vs_minimum || 0;
                if (savings > maxSavings) {
                  maxSavings = savings;
                  bestScenario = scenario;
                }
              });

              return selectedStrategy === bestScenario && maxSavings > 0;
            })()}
          />
        )}
      </div>
    </div>
  );
}
