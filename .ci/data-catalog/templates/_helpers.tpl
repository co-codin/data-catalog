{{/*
Expand the name of the chart.
*/}}
{{- define "data-catalog.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "data-catalog.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "data-catalog.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Extract environment from release name with fallback
*/}}
{{- define "chart.environment" -}}
{{- $parts := split "-" .Release.Name -}}
{{- if gt (len $parts) 2 -}}
  {{- $lastIndex := sub (len $parts) 1 -}}
  {{- $env := index $parts (printf "%d" $lastIndex) -}}
  {{- printf "%s" $env -}}
{{- else -}}
  {{- printf "unknown" -}}
{{- end -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "data-catalog.labels" -}}
helm.sh/chart: {{ include "data-catalog.chart" . }}
{{ include "data-catalog.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
environment: {{ include "chart.environment" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "data-catalog.selectorLabels" -}}
app.kubernetes.io/name: {{ include "data-catalog.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "data-catalog.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "data-catalog.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
