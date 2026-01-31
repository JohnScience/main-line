# MinIO Helm Chart

This Helm chart deploys MinIO object storage for the main-line application.

## Installation

```bash
helm install minio ./k8s/minio
```

## Configuration

The following table lists the configurable parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of MinIO replicas | `1` |
| `image.repository` | MinIO image repository | `minio/minio` |
| `image.tag` | MinIO image tag | `latest` |
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.apiPort` | MinIO API port | `9000` |
| `service.consolePort` | MinIO console port | `9001` |
| `persistence.enabled` | Enable persistent storage | `true` |
| `persistence.size` | PVC storage size | `10Gi` |
| `auth.rootUser` | MinIO root username | `admin` |
| `auth.rootPassword` | MinIO root password | `admin123` |
| `buckets` | List of buckets to create | `[{name: avatars}]` |

## Custom Values

Create a custom values file:

```yaml
auth:
  rootUser: "myuser"
  rootPassword: "mypassword"

persistence:
  size: 20Gi

buckets:
  - name: avatars
  - name: documents
```

Install with custom values:

```bash
helm install minio ./k8s/minio -f custom-values.yaml
```

## Uninstallation

```bash
helm uninstall minio
```
