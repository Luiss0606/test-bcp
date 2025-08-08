#!/bin/bash

# ========================================
# Script de Despliegue Automatizado a Azure
# ========================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
RESOURCE_GROUP="rg-financial-app"
LOCATION="westus2"
ACR_NAME="acrfinancialapp"
BACKEND_CONTAINER_NAME="financial-backend-aci"
FRONTEND_CONTAINER_NAME="financial-frontend-aci"
BACKEND_DNS_LABEL="financial-backend-app"
FRONTEND_DNS_LABEL="financial-frontend-app"

# Función para imprimir mensajes con color
print_message() {
    echo -e "${2}${1}${NC}"
}

# Función para verificar comandos requeridos
check_requirements() {
    print_message "Verificando requisitos..." "$BLUE"
    
    if ! command -v az &> /dev/null; then
        print_message "Error: Azure CLI no está instalado. Instálalo desde: https://docs.microsoft.com/cli/azure/install-azure-cli" "$RED"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_message "Error: Docker no está instalado. Instálalo desde: https://www.docker.com/get-started" "$RED"
        exit 1
    fi
    
    print_message "✓ Requisitos verificados" "$GREEN"
}

# Función para verificar login de Azure
check_azure_login() {
    print_message "Verificando autenticación de Azure..." "$BLUE"
    
    if ! az account show &> /dev/null; then
        print_message "No estás autenticado en Azure. Iniciando login..." "$YELLOW"
        az login
    else
        ACCOUNT=$(az account show --query name -o tsv)
        print_message "✓ Autenticado en Azure como: $ACCOUNT" "$GREEN"
    fi
}

# Función para cargar variables de entorno
load_env_vars() {
    print_message "Cargando variables de entorno..." "$BLUE"
    
    if [ ! -f .env.production ]; then
        print_message "Error: Archivo .env.production no encontrado" "$RED"
        print_message "Crea un archivo .env.production con las siguientes variables:" "$YELLOW"
        echo "OPENAI_API_KEY=s"
        echo "SUPABASE_URL=https://rzfusmwfkbvcmrhakywa.supabase.co"
        echo "SUPABASE_ANON_KEY=tu_clave_supabase"
        echo "LANGSMITH_TRACING=true"
        echo "LANGSMITH_API_KEY=lsv2_pt_46f..."
        echo "LANGCHAIN_PROJECT=bcp-test"
        echo "LANGSMITH_ENDPOINT=https://api.smith.langchain.com"
        exit 1
    fi
    
    # Cargar variables del archivo .env.production
    export $(cat .env.production | grep -v '^#' | xargs)
    
    # Verificar variables requeridas
    if [ -z "$OPENAI_API_KEY" ] || [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_ANON_KEY" ]; then
        print_message "Error: Faltan variables de entorno requeridas en .env.production" "$RED"
        exit 1
    fi
    
    print_message "✓ Variables de entorno cargadas" "$GREEN"
}

# Función para crear o verificar Resource Group
setup_resource_group() {
    print_message "Configurando Resource Group..." "$BLUE"
    
    if az group show --name $RESOURCE_GROUP &> /dev/null; then
        print_message "✓ Resource Group '$RESOURCE_GROUP' ya existe" "$GREEN"
    else
        print_message "Creando Resource Group '$RESOURCE_GROUP'..." "$YELLOW"
        az group create --name $RESOURCE_GROUP --location $LOCATION
        print_message "✓ Resource Group creado" "$GREEN"
    fi
}

# Función para crear o verificar Container Registry
setup_container_registry() {
    print_message "Configurando Azure Container Registry..." "$BLUE"
    
    if az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP &> /dev/null; then
        print_message "✓ Container Registry '$ACR_NAME' ya existe" "$GREEN"
    else
        print_message "Creando Container Registry '$ACR_NAME'..." "$YELLOW"
        az acr create \
            --resource-group $RESOURCE_GROUP \
            --name $ACR_NAME \
            --sku Basic \
            --admin-enabled true
        print_message "✓ Container Registry creado" "$GREEN"
    fi
    
    # Login en ACR
    print_message "Autenticando en Container Registry..." "$BLUE"
    az acr login --name $ACR_NAME
    print_message "✓ Autenticado en ACR" "$GREEN"
}

# Función para construir y subir imágenes
build_and_push_images() {
    print_message "Construyendo y subiendo imágenes Docker..." "$BLUE"
    
    # Backend
    print_message "Construyendo imagen del backend..." "$YELLOW"
    docker build --platform linux/amd64 -t $ACR_NAME.azurecr.io/financial-backend:latest ./backend
    
    print_message "Subiendo imagen del backend..." "$YELLOW"
    docker push $ACR_NAME.azurecr.io/financial-backend:latest
    print_message "✓ Backend subido" "$GREEN"
    
    # Frontend
    print_message "Construyendo imagen del frontend..." "$YELLOW"
    docker build --platform linux/amd64 -t $ACR_NAME.azurecr.io/financial-frontend:latest ./frontend
    
    print_message "Subiendo imagen del frontend..." "$YELLOW"
    docker push $ACR_NAME.azurecr.io/financial-frontend:latest
    print_message "✓ Frontend subido" "$GREEN"
}

# Función para desplegar contenedores
deploy_containers() {
    print_message "Desplegando contenedores en Azure..." "$BLUE"
    
    # Obtener credenciales del ACR
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
    
    # Desplegar Backend
    print_message "Desplegando backend..." "$YELLOW"
    
    # Eliminar contenedor existente si existe
    az container delete --name $BACKEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP --yes 2>/dev/null || true
    
    az container create \
        --resource-group $RESOURCE_GROUP \
        --name $BACKEND_CONTAINER_NAME \
        --image $ACR_NAME.azurecr.io/financial-backend:latest \
        --registry-login-server $ACR_NAME.azurecr.io \
        --registry-username $ACR_NAME \
        --registry-password "$ACR_PASSWORD" \
        --dns-name-label $BACKEND_DNS_LABEL \
        --ports 8000 \
        --cpu 1 \
        --memory 1.5 \
        --os-type Linux \
        --location $LOCATION \
        --environment-variables \
            SUPABASE_URL="$SUPABASE_URL" \
            SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
            OPENAI_API_KEY="$OPENAI_API_KEY" \
            LOAD_SAMPLE_DATA="true" \
            LANGSMITH_TRACING="true" \
            LANGSMITH_API_KEY="$LANGSMITH_API_KEY" \
            LANGCHAIN_PROJECT="$LANGCHAIN_PROJECT" \
            LANGSMITH_ENDPOINT="$LANGSMITH_ENDPOINT" \
            DEBUG="false"
    
    print_message "✓ Backend desplegado" "$GREEN"
    
    # Desplegar Frontend
    print_message "Desplegando frontend..." "$YELLOW"
    
    # Eliminar contenedor existente si existe
    az container delete --name $FRONTEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP --yes 2>/dev/null || true
    
    az container create \
        --resource-group $RESOURCE_GROUP \
        --name $FRONTEND_CONTAINER_NAME \
        --image $ACR_NAME.azurecr.io/financial-frontend:latest \
        --registry-login-server $ACR_NAME.azurecr.io \
        --registry-username $ACR_NAME \
        --registry-password "$ACR_PASSWORD" \
        --dns-name-label $FRONTEND_DNS_LABEL \
        --ports 80 \
        --cpu 0.5 \
        --memory 1 \
        --os-type Linux \
        --location $LOCATION
    
    print_message "✓ Frontend desplegado" "$GREEN"
}

# Función para verificar el despliegue
verify_deployment() {
    print_message "Verificando el despliegue..." "$BLUE"
    
    # Esperar un momento para que los contenedores inicien
    sleep 10
    
    # Verificar Backend
    BACKEND_URL="http://$BACKEND_DNS_LABEL.$LOCATION.azurecontainer.io:8000"
    if curl -s "$BACKEND_URL/api/v1/health" | grep -q "healthy"; then
        print_message "✓ Backend funcionando correctamente" "$GREEN"
    else
        print_message "⚠ Backend puede estar iniciándose, verifica en unos momentos" "$YELLOW"
    fi
    
    # Verificar Frontend
    FRONTEND_URL="http://$FRONTEND_DNS_LABEL.$LOCATION.azurecontainer.io"
    if curl -s "$FRONTEND_URL" | grep -q "<!doctype html>"; then
        print_message "✓ Frontend funcionando correctamente" "$GREEN"
    else
        print_message "⚠ Frontend puede estar iniciándose, verifica en unos momentos" "$YELLOW"
    fi
}

# Función para mostrar información de acceso
show_access_info() {
    echo ""
    print_message "========================================" "$GREEN"
    print_message "¡DESPLIEGUE COMPLETADO CON ÉXITO!" "$GREEN"
    print_message "========================================" "$GREEN"
    echo ""
    print_message "URLs de Acceso:" "$BLUE"
    echo ""
    print_message "Frontend (Aplicación Web):" "$YELLOW"
    echo "  http://$FRONTEND_DNS_LABEL.$LOCATION.azurecontainer.io"
    echo ""
    print_message "Backend (API):" "$YELLOW"
    echo "  http://$BACKEND_DNS_LABEL.$LOCATION.azurecontainer.io:8000"
    echo ""
    print_message "Documentación API:" "$YELLOW"
    echo "  http://$BACKEND_DNS_LABEL.$LOCATION.azurecontainer.io:8000/docs"
    echo ""
    print_message "Resource Group: $RESOURCE_GROUP" "$BLUE"
    print_message "Container Registry: $ACR_NAME.azurecr.io" "$BLUE"
    echo ""
    print_message "Para ver los logs de los contenedores:" "$YELLOW"
    echo "  az container logs --name $BACKEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP"
    echo "  az container logs --name $FRONTEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP"
    echo ""
}

# Función principal
main() {
    clear
    print_message "========================================" "$BLUE"
    print_message "Script de Despliegue a Azure" "$BLUE"
    print_message "Financial Restructuring Assistant" "$BLUE"
    print_message "========================================" "$BLUE"
    echo ""
    
    # Ejecutar pasos
    check_requirements
    check_azure_login
    load_env_vars
    setup_resource_group
    setup_container_registry
    build_and_push_images
    deploy_containers
    verify_deployment
    show_access_info
}

# Función para actualizar solo las imágenes
update_deployment() {
    clear
    print_message "========================================" "$BLUE"
    print_message "Actualización de Despliegue en Azure" "$BLUE"
    print_message "========================================" "$BLUE"
    echo ""
    
    check_requirements
    check_azure_login
    load_env_vars
    
    print_message "Actualizando imágenes y contenedores..." "$BLUE"
    
    # Login en ACR
    print_message "Autenticando en Container Registry..." "$BLUE"
    az acr login --name $ACR_NAME
    print_message "✓ Autenticado en ACR" "$GREEN"
    
    # Construir y subir nuevas imágenes
    build_and_push_images
    
    # Obtener credenciales del ACR
    ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)
    
    # Actualizar Backend
    print_message "Actualizando backend..." "$YELLOW"
    az container restart --name $BACKEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP 2>/dev/null || {
        print_message "Recreando contenedor backend con nueva imagen..." "$YELLOW"
        az container delete --name $BACKEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP --yes
        
        az container create \
            --resource-group $RESOURCE_GROUP \
            --name $BACKEND_CONTAINER_NAME \
            --image $ACR_NAME.azurecr.io/financial-backend:latest \
            --registry-login-server $ACR_NAME.azurecr.io \
            --registry-username $ACR_NAME \
            --registry-password "$ACR_PASSWORD" \
            --dns-name-label $BACKEND_DNS_LABEL \
            --ports 8000 \
            --cpu 1 \
            --memory 1.5 \
            --os-type Linux \
            --location $LOCATION \
            --environment-variables \
                SUPABASE_URL="$SUPABASE_URL" \
                SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
                OPENAI_API_KEY="$OPENAI_API_KEY" \
                LOAD_SAMPLE_DATA="false" \
                DEBUG="false"
    }
    print_message "✓ Backend actualizado" "$GREEN"
    
    # Actualizar Frontend
    print_message "Actualizando frontend..." "$YELLOW"
    az container restart --name $FRONTEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP 2>/dev/null || {
        print_message "Recreando contenedor frontend con nueva imagen..." "$YELLOW"
        az container delete --name $FRONTEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP --yes
        
        az container create \
            --resource-group $RESOURCE_GROUP \
            --name $FRONTEND_CONTAINER_NAME \
            --image $ACR_NAME.azurecr.io/financial-frontend:latest \
            --registry-login-server $ACR_NAME.azurecr.io \
            --registry-username $ACR_NAME \
            --registry-password "$ACR_PASSWORD" \
            --dns-name-label $FRONTEND_DNS_LABEL \
            --ports 80 \
            --cpu 0.5 \
            --memory 1 \
            --os-type Linux \
            --location $LOCATION
    }
    print_message "✓ Frontend actualizado" "$GREEN"
    
    verify_deployment
    show_access_info
}

# Función para actualización rápida (solo rebuild y restart)
quick_update() {
    clear
    print_message "========================================" "$BLUE"
    print_message "Actualización Rápida de Azure" "$BLUE"
    print_message "========================================" "$BLUE"
    echo ""
    
    check_requirements
    
    # Determinar qué actualizar
    WHAT_TO_UPDATE="${2:-both}"
    
    print_message "Actualizando: $WHAT_TO_UPDATE" "$BLUE"
    
    # Login en ACR
    print_message "Autenticando en Container Registry..." "$BLUE"
    az acr login --name $ACR_NAME
    print_message "✓ Autenticado en ACR" "$GREEN"
    
    # Actualizar según la selección
    case "$WHAT_TO_UPDATE" in
        backend)
            print_message "Construyendo y subiendo backend..." "$YELLOW"
            docker build --platform linux/amd64 -t $ACR_NAME.azurecr.io/financial-backend:latest ./backend
            docker push $ACR_NAME.azurecr.io/financial-backend:latest
            print_message "✓ Backend actualizado en ACR" "$GREEN"
            
            print_message "Reiniciando contenedor backend..." "$YELLOW"
            az container restart --name $BACKEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP
            print_message "✓ Backend reiniciado" "$GREEN"
            ;;
        frontend)
            print_message "Construyendo y subiendo frontend..." "$YELLOW"
            docker build --platform linux/amd64 -t $ACR_NAME.azurecr.io/financial-frontend:latest ./frontend
            docker push $ACR_NAME.azurecr.io/financial-frontend:latest
            print_message "✓ Frontend actualizado en ACR" "$GREEN"
            
            print_message "Reiniciando contenedor frontend..." "$YELLOW"
            az container restart --name $FRONTEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP
            print_message "✓ Frontend reiniciado" "$GREEN"
            ;;
        both|"")
            print_message "Construyendo y subiendo ambas imágenes..." "$YELLOW"
            docker build --platform linux/amd64 -t $ACR_NAME.azurecr.io/financial-backend:latest ./backend
            docker push $ACR_NAME.azurecr.io/financial-backend:latest
            docker build --platform linux/amd64 -t $ACR_NAME.azurecr.io/financial-frontend:latest ./frontend
            docker push $ACR_NAME.azurecr.io/financial-frontend:latest
            print_message "✓ Imágenes actualizadas en ACR" "$GREEN"
            
            print_message "Reiniciando contenedores..." "$YELLOW"
            az container restart --name $BACKEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP
            az container restart --name $FRONTEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP
            print_message "✓ Contenedores reiniciados" "$GREEN"
            ;;
        *)
            print_message "Opción inválida. Usa 'backend', 'frontend' o 'both'" "$RED"
            exit 1
            ;;
    esac
    
    echo ""
    print_message "========================================" "$GREEN"
    print_message "¡Actualización Completada!" "$GREEN"
    print_message "========================================" "$GREEN"
    echo ""
    print_message "Los cambios están siendo aplicados. Espera 30-60 segundos para que los contenedores se reinicien completamente." "$YELLOW"
    echo ""
    print_message "URLs de acceso:" "$BLUE"
    echo "  Frontend: http://$FRONTEND_DNS_LABEL.$LOCATION.azurecontainer.io"
    echo "  Backend: http://$BACKEND_DNS_LABEL.$LOCATION.azurecontainer.io:8000"
    echo ""
}

# Manejo de argumentos opcionales
case "${1:-}" in
    --update)
        update_deployment
        ;;
    --quick-update|--qu)
        quick_update "$@"
        ;;
    --clean)
        print_message "Limpiando recursos de Azure..." "$YELLOW"
        az group delete --name $RESOURCE_GROUP --yes --no-wait
        print_message "✓ Eliminación de recursos iniciada" "$GREEN"
        exit 0
        ;;
    --status)
        print_message "Estado de los contenedores:" "$BLUE"
        az container list --resource-group $RESOURCE_GROUP --output table
        exit 0
        ;;
    --logs)
        if [ -z "${2:-}" ]; then
            print_message "Uso: $0 --logs [backend|frontend]" "$YELLOW"
            exit 1
        fi
        case "$2" in
            backend)
                az container logs --name $BACKEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP --follow
                ;;
            frontend)
                az container logs --name $FRONTEND_CONTAINER_NAME --resource-group $RESOURCE_GROUP --follow
                ;;
            *)
                print_message "Opción inválida. Usa 'backend' o 'frontend'" "$RED"
                exit 1
                ;;
        esac
        exit 0
        ;;
    --help)
        echo "Uso: $0 [opciones]"
        echo ""
        echo "Opciones de despliegue:"
        echo "  (sin opciones)       Ejecutar despliegue completo (primera vez)"
        echo "  --update             Actualizar despliegue existente (reconstruir y redesplegar)"
        echo "  --quick-update [backend|frontend|both]  Actualización rápida (solo rebuild y restart)"
        echo "  --qu [backend|frontend|both]            Alias corto para --quick-update"
        echo ""
        echo "Opciones de mantenimiento:"
        echo "  --status             Ver estado de los contenedores"
        echo "  --logs [backend|frontend]  Ver logs de un contenedor"
        echo "  --clean              Eliminar todos los recursos de Azure"
        echo "  --help               Mostrar esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  $0                   # Despliegue inicial completo"
        echo "  $0 --update          # Actualizar todo después de cambios"
        echo "  $0 --qu backend      # Actualización rápida solo del backend"
        echo "  $0 --qu frontend     # Actualización rápida solo del frontend"
        echo "  $0 --qu              # Actualización rápida de ambos"
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_message "Opción no reconocida: $1" "$RED"
        echo "Usa $0 --help para ver las opciones disponibles"
        exit 1
        ;;
esac
