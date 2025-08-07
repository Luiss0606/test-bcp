import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { BarChart3 } from 'lucide-react';

interface ScenarioData {
  total_payoff_months: number;
  total_interest: number;
  total_payments: number;
  savings_vs_minimum: number;
  total_monthly_payment: number;
}

interface PaymentComparisonChartProps {
  scenarios: {
    minimum: ScenarioData;
    optimized: ScenarioData;
    consolidation: ScenarioData;
  };
  formatCurrency: (amount: number) => string;
}

export function PaymentComparisonChart({ scenarios, formatCurrency }: PaymentComparisonChartProps) {
  // Generate cumulative payment data for each scenario
  const generatePaymentData = () => {
    const maxMonths = Math.max(
      scenarios.minimum.total_payoff_months,
      scenarios.optimized.total_payoff_months,
      scenarios.consolidation.total_payoff_months
    );

    const data = [];
    
    // Calculate monthly payments for each scenario
    const monthlyMinimum = scenarios.minimum.total_payments / scenarios.minimum.total_payoff_months;
    const monthlyOptimized = scenarios.optimized.total_payments / scenarios.optimized.total_payoff_months;
    const monthlyConsolidation = scenarios.consolidation.total_payments / scenarios.consolidation.total_payoff_months;
    
    // Track cumulative payments for each scenario
    let cumulativeMinimum = 0;
    let cumulativeOptimized = 0;
    let cumulativeConsolidation = 0;
    
    for (let month = 1; month <= maxMonths; month++) {
      // Add monthly payment to cumulative if scenario is still active
      if (month <= scenarios.minimum.total_payoff_months) {
        cumulativeMinimum += monthlyMinimum;
      }
      if (month <= scenarios.optimized.total_payoff_months) {
        cumulativeOptimized += monthlyOptimized;
      }
      if (month <= scenarios.consolidation.total_payoff_months) {
        cumulativeConsolidation += monthlyConsolidation;
      }

      const dataPoint: any = {
        mes: month,
        'Pago Mínimo': cumulativeMinimum,
        'Plan Optimizado': cumulativeOptimized,
        'Consolidación': cumulativeConsolidation,
      };
      
      data.push(dataPoint);
    }
    
    return data;
  };

  const chartData = generatePaymentData();

  // Custom tooltip formatter
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-border rounded-lg shadow-lg">
          <p className="font-medium mb-2">{`Pagado hasta el mes ${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${formatCurrency(entry.value)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Custom legend formatter
  const renderLegend = (props: any) => {
    const { payload } = props;
    return (
      <div className="flex justify-center space-x-6 mt-4">
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center space-x-2">
            <div 
              className="w-4 h-4 rounded"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-sm font-medium text-muted-foreground">
              {entry.value}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <Card className="shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center text-xl">
          <BarChart3 className="w-6 h-6 mr-2 text-primary" />
          Comparación de Pagos Acumulados
        </CardTitle>
        <p className="text-sm text-muted-foreground">
          Visualización del progreso acumulativo de pagos a lo largo del tiempo para cada estrategia
        </p>
      </CardHeader>
      <CardContent className="p-6">
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 20,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis 
                dataKey="mes" 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend content={renderLegend} />
              
              {/* Pago Mínimo - Orange/Amber colors */}
              <Area
                type="monotone"
                dataKey="Pago Mínimo"
                stackId="1"
                stroke="#f59e0b"
                fill="#fef3c7"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, stroke: "#f59e0b", strokeWidth: 2 }}
              />
              
              {/* Plan Optimizado - Blue colors */}
              <Area
                type="monotone"
                dataKey="Plan Optimizado"
                stackId="2"
                stroke="#3b82f6"
                fill="#dbeafe"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, stroke: "#3b82f6", strokeWidth: 2 }}
              />
              
              {/* Consolidación - Green colors */}
              <Area
                type="monotone"
                dataKey="Consolidación"
                stackId="3"
                stroke="#10b981"
                fill="#d1fae5"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, stroke: "#10b981", strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Summary statistics */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-amber-50 rounded-lg border border-amber-200">
            <h4 className="font-medium text-amber-800 mb-1">Pago Mínimo</h4>
            <p className="text-2xl font-bold text-amber-700">
              {formatCurrency(scenarios.minimum.total_payments)}
            </p>
            <p className="text-sm text-amber-600">
              Total en {scenarios.minimum.total_payoff_months} meses
            </p>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-medium text-blue-800 mb-1">Plan Optimizado</h4>
            <p className="text-2xl font-bold text-blue-700">
              {formatCurrency(scenarios.optimized.total_payments)}
            </p>
            <p className="text-sm text-blue-600">
              Total en {scenarios.optimized.total_payoff_months} meses
            </p>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
            <h4 className="font-medium text-green-800 mb-1">Consolidación</h4>
            <p className="text-2xl font-bold text-green-700">
              {formatCurrency(scenarios.consolidation.total_payments)}
            </p>
            <p className="text-sm text-green-600">
              Total en {scenarios.consolidation.total_payoff_months} meses
            </p>
          </div>
        </div>

        {/* Key insights */}
        <div className="mt-6 p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium mb-2">💡 Puntos Clave:</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Las líneas muestran el progreso acumulativo de pagos a lo largo del tiempo</li>
            <li>• Una línea más empinada indica pagos mensuales más altos</li>
            <li>• Una línea más corta indica menos tiempo para pagar completamente</li>
            <li>• La estrategia más eficiente termina con el menor total pagado</li>
            <li>• Puedes ver exactamente cuánto habrás pagado en cualquier mes específico</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
