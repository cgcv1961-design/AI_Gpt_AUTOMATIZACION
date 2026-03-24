# 🧠 AI_Gpt_AUTOMATIZACION

Plataforma de análisis inteligente de contratos basada en Inteligencia Artificial + lógica determinista.

---

## 🎯 Objetivo

Analizar documentos legales (y audiovisuales) para:

- Extraer información estructurada
- Detectar riesgos
- Evaluar equilibrio contractual
- Generar informes profesionales para clientes

---

## 💡 Valor diferencial

Este sistema combina:

- IA generativa (interpretación semántica)
- Lógica determinista en Python (validación y scoring)
- Estructura JSON auditable

👉 A diferencia de soluciones puramente basadas en IA, este enfoque permite:

- Transparencia en resultados
- Explicabilidad
- Mayor confiabilidad profesional

---

## ⚙️ Cómo funciona

El sistema sigue este flujo:

1. Ingesta de contrato (PDF / DOCX / TXT)
2. Conversión a JSON estructurado
3. Detección automática de vertical
4. Análisis con IA (LLM)
5. Aplicación de scoring determinista
6. Generación de resultados:
   - JSON técnico
   - Informe Word profesional

---

## 🏗 Arquitectura del proyecto


AI_Gpt_AUTOMATIZACION/
│
├── api/ # API FastAPI
├── core/ # Lógica base (scoring, normalización)
├── services/ # Orquestación
├── verticales/
│ ├── general/
│ └── audiovisual/
├── utils/ # Funciones auxiliares
├── tools/ # Conversión de documentos
├── reportes_generator/ # Generación de informes Word
├── demo/ # Ejecución local
│
├── main.py # Punto de entrada
├── config.py # Configuración
└── analizador.py # Motor principal


---

## 🚀 Ejecución local

### 1. Clonar repositorio

```bash
git clone https://github.com/cgcv1961-design/AI_Gpt_AUTOMATIZACION.git
cd AI_Gpt_AUTOMATIZACION
2. Instalar dependencias
pip install -r requirements.txt
3. Ejecutar demo
python demo/ejecutar_demo.py
4. Ejecutar API
uvicorn api.api:app --reload

Acceder a:

http://127.0.0.1:8000/docs

🧪 Ejemplo de flujo
Cargar contrato
Ejecutar análisis
Obtener:
JSON estructurado
Informe Word
Evaluación de riesgos
📊 Output del sistema

El sistema genera:

📄 JSON técnico estructurado
🧾 Informe Word profesional
📈 Evaluación de riesgo
🧠 Recomendaciones estratégicas
🧩 Verticales actuales
🔹 GENERAL
Contratos estándar
Análisis profesional balanceado
🔹 AUDIOVISUAL
Contratos de producción
Derechos de imagen
Licencias
Relación productor / artista
📌 Casos de uso
Análisis de contratos de alquiler
Evaluación de contratos audiovisuales
Asistencia a abogados
Validación pre-firma para empresas
🔐 Seguridad

El proyecto utiliza .gitignore para evitar subir:

Datos sensibles (.env)
Documentos de prueba
Output generado
🌐 Deploy (Render)

El sistema está preparado para desplegarse en:

https://render.com

Flujo:

Subir código a GitHub
Conectar repositorio en Render
Configurar variables de entorno
Deploy automático
🧠 Filosofía del proyecto

Este sistema no reemplaza al profesional.

👉 Lo potencia.

IA interpreta
Python valida
El humano decide
👨‍💻 Autor
---
Gustavo – Consultoría en automatización e IA aplicada

🚀 Estado del proyecto

✔ MVP funcional
✔ API operativa
✔ Arquitectura escalable
✔ Listo para demo y clientes

🔮 Próximos pasos
Mejora del scoring
Nuevas verticales
Interfaz web
Integración con clientes reales

---
---

⭐ Si este proyecto te resulta útil, no olvides darle una estrella en GitHub.
