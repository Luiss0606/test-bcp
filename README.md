# Financial Restructuring Assistant

AI-powered financial debt restructuring assistant for bank customers. Complete full-stack implementation with React frontend and FastAPI backend, using modern technologies like Bun, shadcn/ui, LangChain agents, and OpenAI GPT models with Spanish-language focus.

## 🚀 Aplicación en Vivo

La aplicación está actualmente desplegada en Azure y disponible en:

- 🌐 **Aplicación Web**: http://financial-frontend-app.westus2.azurecontainer.io
- 🔧 **API Backend**: http://financial-backend-app.westus2.azurecontainer.io:8000
- 📚 **Documentación API**: http://financial-backend-app.westus2.azurecontainer.io:8000/docs

**Cliente de prueba**: Usa `CU-001` para probar la aplicación con datos de ejemplo.

## 🚀 Quick Start - Ejecución Local

### Opción 1: Docker Compose (Recomendado - Todo en uno)

**Pre-requisitos:**
- Docker Desktop instalado ([Descargar aquí](https://www.docker.com/products/docker-desktop/))
- Git instalado
- Clave API de OpenAI ([Obtener aquí](https://platform.openai.com/api-keys))

**Pasos:**

1. **Clonar el repositorio:**
```bash
git clone <repository>
cd bcp_test
```

2. **Configurar variables de entorno:**
```bash
# Crear archivo .env en la raíz del proyecto
cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=tu_clave_api_de_openai_aqui

# Database Configuration
DATABASE_URL=sqlite:///app/database/financial_assistant.db

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
LOAD_SAMPLE_DATA=true

# LangChain Configuration (opcional)
LANGSMITH_TRACING=false
EOF
```

3. **Ejecutar la aplicación completa:**
```bash
# Construir y ejecutar todos los servicios
docker-compose up --build

# O ejecutar en segundo plano
docker-compose up --build -d
```

4. **Acceder a la aplicación:**
- 🌐 **Frontend (Interfaz de Usuario)**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📚 **Documentación API**: http://localhost:8000/docs

5. **Cargar datos de prueba (primera vez):**
```bash
# Una vez que el backend esté ejecutándose
curl -X POST "http://localhost:8000/api/v1/load-data"
```

6. **Detener la aplicación:**
```bash
# Si está ejecutándose en primer plano: Ctrl+C
# Si está en segundo plano:
docker-compose down

# Para eliminar también los volúmenes de datos:
docker-compose down -v
```

### Opción 2: Desarrollo Local Nativo

#### Pre-requisitos

**Frontend:**
- Node.js 18+ ([Descargar](https://nodejs.org/))
- Bun ([Instalar](https://bun.sh/))

**Backend:**
- Python 3.11+ ([Descargar](https://www.python.org/))
- UV package manager ([Instalar](https://docs.astral.sh/uv/))

#### Frontend - Desarrollo Local

```bash
# 1. Navegar al directorio frontend
cd frontend

# 2. Instalar Bun si no lo tienes
curl -fsSL https://bun.sh/install | bash
# Reiniciar terminal o ejecutar: source ~/.bashrc

# 3. Instalar dependencias
bun install

# 4. Configurar backend URL (opcional si el backend corre en otro puerto)
# Editar vite.config.ts si es necesario

# 5. Ejecutar en modo desarrollo
bun run dev

# La aplicación estará disponible en http://localhost:5173
```

**Comandos útiles del frontend:**
```bash
# Construir para producción
bun run build

# Previsualizar build de producción
bun run preview

# Linter
bun run lint

# Verificar tipos de TypeScript
bun run type-check
```

#### Backend - Desarrollo Local

```bash
# 1. Navegar al directorio backend
cd backend

# 2. Instalar UV si no lo tienes
curl -LsSf https://astral.sh/uv/install.sh | sh
# Reiniciar terminal o ejecutar: source ~/.local/bin/env

# 3. Crear y configurar .env en el directorio backend
cat > .env << EOF
OPENAI_API_KEY=tu_clave_api_de_openai_aqui
DATABASE_URL=sqlite:///./financial_assistant.db
DEBUG=true
LOG_LEVEL=INFO
LOAD_SAMPLE_DATA=true
EOF

# 4. Instalar dependencias del proyecto
uv sync

# 5. Ejecutar el servidor de desarrollo
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# El API estará disponible en http://localhost:8000
```

**Comandos útiles del backend:**
```bash
# Cargar datos de prueba
curl -X POST "http://localhost:8000/api/v1/load-data"

# Ejecutar tests
uv run pytest

# Formatear código
uv run black .
uv run isort .

# Verificar tipos
uv run mypy app

# Ver logs en tiempo real
tail -f logs/app.log
```

### Opción 3: Desarrollo Híbrido

Puedes ejecutar el backend con Docker y el frontend localmente (o viceversa):

**Backend con Docker + Frontend local:**
```bash
# Terminal 1: Backend
docker-compose up backend

# Terminal 2: Frontend
cd frontend
bun run dev
```

**Frontend con Docker + Backend local:**
```bash
# Terminal 1: Frontend
docker-compose up frontend

# Terminal 2: Backend
cd backend
uv run uvicorn app.main:app --reload
```

## 🔧 Configuración

### Variables de Entorno Importantes

| Variable | Descripción | Requerido | Valor por defecto |
|----------|-------------|-----------|-------------------|
| `OPENAI_API_KEY` | Clave API de OpenAI | ✅ Sí | - |
| `DATABASE_URL` | URL de conexión a base de datos | No | `sqlite:///./financial_assistant.db` |
| `LOAD_SAMPLE_DATA` | Cargar datos de ejemplo al iniciar | No | `false` |
| `DEBUG` | Modo debug (más logs) | No | `false` |
| `LOG_LEVEL` | Nivel de logging | No | `INFO` |
| `LANGSMITH_TRACING` | Habilitar tracing con LangSmith | No | `false` |
| `CORS_ORIGINS` | Orígenes CORS permitidos | No | `["http://localhost:3000", "http://localhost:5173"]` |

### Variables de Entorno del Frontend

Para que el frontend apunte al backend correcto en producción o staging, usa la variable `VITE_API_URL`.

- Docker Compose (ya configurado): se pasa como build-arg `VITE_API_URL` al frontend.
- Desarrollo local (frontend): crea `frontend/.env.local` con:

```bash
VITE_API_URL=http://localhost:8000
```

Si despliegas en Azure con dominios separados, por ejemplo:

```bash
VITE_API_URL=http://financial-backend-app.westus2.azurecontainer.io:8000
```

El frontend también detecta automáticamente, en ausencia de `VITE_API_URL`, el backend en:
- Localhost: `http://localhost:8000`
- Azure (por convención): reemplaza "frontend" por "backend" y usa puerto 8000

### Puertos Utilizados

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| Frontend | 3000 | React app (Docker) |
| Frontend (desarrollo) | 5173 | Vite dev server |
| Backend API | 8000 | FastAPI server |

## 🧪 Pruebas Rápidas

### 1. Verificar que el backend está funcionando:
```bash
curl http://localhost:8000/api/v1/health
# Respuesta esperada: {"status":"healthy","database":"connected"}
```

### 2. Cargar datos de ejemplo:
```bash
curl -X POST http://localhost:8000/api/v1/load-data
# Respuesta: {"message":"Sample data loaded successfully","customers_count":3}
```

### 3. Obtener lista de clientes:
```bash
curl http://localhost:8000/api/v1/customers
# Respuesta: Lista de clientes con sus deudas
```

### 4. Analizar deuda de un cliente:
```bash
curl -X POST http://localhost:8000/api/v1/customers/CU-001/analyze
# Respuesta: Análisis completo con 3 escenarios
```

## 🐛 Solución de Problemas Comunes

### Error: "OpenAI API key not found"
**Solución:** Asegúrate de que la variable `OPENAI_API_KEY` esté configurada en tu archivo `.env`

### Error: "Cannot connect to database"
**Solución:** 
- Con Docker: Verifica que el contenedor esté ejecutándose
- Local: Verifica que el path de la base de datos sea correcto

### Error: "Port 8000 already in use"
**Solución:**
```bash
# Encontrar proceso usando el puerto
lsof -i :8000
# Terminar el proceso
kill -9 <PID>
# O cambiar el puerto en el comando uvicorn
uv run uvicorn app.main:app --reload --port 8001
```

### Error: "CORS blocked"
**Solución:** Verifica que el frontend esté accediendo al backend en el puerto correcto (8000)

### Frontend no puede conectar con backend
**Solución:** 
1. Verifica que el backend esté ejecutándose
2. Revisa la configuración del proxy en `frontend/vite.config.ts`
3. Asegúrate de usar las URLs correctas

### Docker build muy lento
**Solución:** 
- Usa Docker BuildKit: `DOCKER_BUILDKIT=1 docker-compose build`
- Limpia caché: `docker system prune -a`

## ☁️ Despliegue en Azure

### Despliegue Automatizado con Script

El proyecto incluye un script automatizado para desplegar la aplicación completa en Azure Container Instances.

#### Pre-requisitos para Azure

1. **Azure CLI instalado** ([Instalar aquí](https://docs.microsoft.com/cli/azure/install-azure-cli))
2. **Cuenta de Azure activa** ([Crear cuenta gratuita](https://azure.microsoft.com/free/))
3. **Docker instalado** para construir las imágenes
4. **Archivo .env configurado** con las claves necesarias

#### Despliegue Rápido

```bash
# 1. Asegúrate de estar en la raíz del proyecto
cd bcp_test

# 2. Ejecutar el script de despliegue
./deploy-to-azure.sh

# El script automáticamente:
# - Verifica requisitos y autenticación
# - Crea los recursos necesarios en Azure
# - Construye y sube las imágenes Docker
# - Despliega los contenedores
# - Verifica el despliegue
# - Muestra las URLs de acceso
```

#### Actualizar Cambios en Azure

Cuando hagas cambios en tu código y quieras actualizar el despliegue:

```bash
# Actualización completa (reconstruye y redespliega todo)
./deploy-to-azure.sh --update

# Actualización rápida de ambos servicios
./deploy-to-azure.sh --qu

# Actualización rápida solo del backend
./deploy-to-azure.sh --qu backend

# Actualización rápida solo del frontend
./deploy-to-azure.sh --qu frontend
```

**Diferencias entre tipos de actualización:**
- `--update`: Reconstruye imágenes, las sube y recrea los contenedores (más seguro, ~3-5 min)
- `--qu` (quick-update): Reconstruye imágenes, las sube y reinicia contenedores (más rápido, ~2-3 min)

#### Comandos de Mantenimiento

```bash
# Ver estado de los contenedores
./deploy-to-azure.sh --status

# Ver logs del backend en tiempo real
./deploy-to-azure.sh --logs backend

# Ver logs del frontend en tiempo real
./deploy-to-azure.sh --logs frontend

# Eliminar todos los recursos de Azure
./deploy-to-azure.sh --clean

# Ver ayuda completa
./deploy-to-azure.sh --help
```

#### Flujo de Trabajo Típico

```bash
# 1. Primera vez - Despliegue inicial completo
./deploy-to-azure.sh

# 2. Desarrollo local
# ... hacer cambios en el código ...

# 3. Probar localmente
docker-compose up --build

# 4. Actualizar en Azure después de verificar que todo funciona
./deploy-to-azure.sh --qu

# 5. Verificar logs si hay problemas
./deploy-to-azure.sh --logs backend
./deploy-to-azure.sh --logs frontend

# 6. Ver estado de los contenedores
./deploy-to-azure.sh --status
```

#### URLs de Producción en Azure

Después del despliegue exitoso, tu aplicación estará disponible en:

- **Frontend**: `http://financial-frontend-app.westus2.azurecontainer.io`
- **Backend API**: `http://financial-backend-app.westus2.azurecontainer.io:8000`
- **API Docs**: `http://financial-backend-app.westus2.azurecontainer.io:8000/docs`

#### Arquitectura en Azure

```mermaid
graph TB
    subgraph "Azure Cloud"
        subgraph "Resource Group: rg-financial-app"
            ACR[Azure Container Registry<br/>acrfinancialapp]
            
            subgraph "Container Instances"
                Backend[Backend Container<br/>1 CPU, 1.5GB RAM<br/>Port: 8000]
                Frontend[Frontend Container<br/>0.5 CPU, 1GB RAM<br/>Port: 80]
            end
            
            Logs[Azure Monitor<br/>Log Analytics]
        end
        
        subgraph "External Services"
            Supabase[Supabase DB]
            OpenAI[OpenAI API]
        end
    end
    
    User[Usuario] --> Frontend
    Frontend --> Backend
    Backend --> Supabase
    Backend --> OpenAI
    Backend --> Logs
    Frontend --> Logs
    ACR --> Backend
    ACR --> Frontend
```

#### Configuración de Recursos Azure

| Recurso | Nombre | Tipo | Especificaciones |
|---------|--------|------|------------------|
| Resource Group | `rg-financial-app` | - | West US 2 |
| Container Registry | `acrfinancialapp` | Basic | Admin enabled |
| Backend Container | `financial-backend-aci` | Linux | 1 CPU, 1.5GB RAM |
| Frontend Container | `financial-frontend-aci` | Linux | 0.5 CPU, 1GB RAM |

#### Costos Estimados

Los costos aproximados en Azure (región West US 2):

- **Container Registry Basic**: ~$5/mes
- **Backend Container**: ~$35/mes (1 CPU, 1.5GB)
- **Frontend Container**: ~$20/mes (0.5 CPU, 1GB)
- **Total estimado**: ~$60/mes

*Nota: Los precios pueden variar. Consulta la [calculadora de precios de Azure](https://azure.microsoft.com/pricing/calculator/) para estimaciones actualizadas.*

#### Monitoreo y Mantenimiento

##### Ver métricas en Azure Portal

1. Ir a [Azure Portal](https://portal.azure.com)
2. Navegar a Resource Group: `rg-financial-app`
3. Seleccionar el contenedor deseado
4. Ver métricas de CPU, memoria y red

##### Comandos de mantenimiento con Azure CLI

```bash
# Reiniciar un contenedor
az container restart --name financial-backend-aci --resource-group rg-financial-app

# Escalar CPU/Memoria (requiere recrear el contenedor)
az container delete --name financial-backend-aci --resource-group rg-financial-app --yes
az container create ... # con nuevas especificaciones

# Ver eventos del contenedor
az container show --name financial-backend-aci --resource-group rg-financial-app --query events

# Exportar logs
az container logs --name financial-backend-aci --resource-group rg-financial-app > backend-logs.txt
```

#### Seguridad en Producción

Para un entorno de producción, considera:

1. **Usar Azure Key Vault** para almacenar secretos
2. **Configurar Azure Application Gateway** para SSL/TLS
3. **Implementar Azure AD** para autenticación
4. **Usar Azure Private Endpoints** para mayor seguridad
5. **Configurar Azure Backup** para respaldos automáticos
6. **Implementar Azure Monitor Alerts** para notificaciones

#### Troubleshooting en Azure

##### El contenedor no inicia
```bash
# Ver eventos del contenedor
az container show --name [container-name] --resource-group rg-financial-app --query instanceView.events

# Ver logs detallados
az container logs --name [container-name] --resource-group rg-financial-app --follow
```

##### Error de autenticación con ACR
```bash
# Re-autenticarse en ACR
az acr login --name acrfinancialapp

# Verificar credenciales
az acr credential show --name acrfinancialapp
```

##### Contenedor se reinicia constantemente
```bash
# Verificar estado
az container show --name [container-name] --resource-group rg-financial-app --query instanceView.state

# Revisar consumo de recursos
az monitor metrics list --resource [container-id] --metric CPUUsage,MemoryUsage
```

## 📊 Arquitectura del Sistema

### Stack Tecnológico

**Frontend:**
- ⚛️ React 18 + TypeScript
- 🎨 Tailwind CSS + shadcn/ui
- ⚡ Vite + Bun
- 📊 Recharts para visualizaciones

**Backend:**
- 🐍 Python 3.11 + FastAPI
- 🤖 LangChain + OpenAI GPT
- 💾 SQLAlchemy + SQLite/PostgreSQL
- 📦 UV package manager

**Infraestructura:**
- 🐳 Docker + Docker Compose
- 📝 Auto-documentación con Swagger

### Flujo de Datos

```mermaid
graph LR
    A[Cliente Web] --> B[Frontend React :3000]
    B --> D[Backend FastAPI :8000]
    D --> E[SQLite DB]
    D --> F[OpenAI API]
    F --> G[GPT-4 Models]
    G --> D
    D --> B
    B --> A
```

## 📚 Documentación Adicional

- **API Interactiva**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Memory Bank**: Ver carpeta `memory-bank/` para documentación del proyecto

## 🤝 Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es para fines demostrativos. Asegúrate de cumplir con las regulaciones financieras de tu jurisdicción.

## 💡 Tips para Desarrollo

- **Hot Reload**: Tanto el frontend como el backend tienen hot reload activado en modo desarrollo
- **Logs**: Revisa los logs en `backend/logs/` para debugging
- **Base de datos**: SQLite para desarrollo, PostgreSQL recomendado para producción
- **Tests**: Ejecuta `uv run pytest` en el backend antes de hacer commit
- **Linting**: Usa `bun run lint` en frontend y `uv run black .` en backend

## 🆘 Soporte

Si encuentras problemas:
1. Revisa la sección de [Solución de Problemas](#-solución-de-problemas-comunes)
2. Verifica los logs del contenedor: `docker-compose logs -f`
3. Asegúrate de tener todas las variables de entorno configuradas
4. Revisa que los puertos no estén en uso
5. Consulta la documentación en `memory-bank/`