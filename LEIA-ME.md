# Desafio Técnico — Engenheiro(a) de Dados Pleno | Motriz

**Cenário 01 — Pipeline de integração de dados de múltiplas redes de ensino**

O enunciado completo, com regras de negócio, entregáveis e critérios de avaliação, está em
`ENUNCIADO_Desafio_Engenharia_de_Dados.docx`. Leia-o antes de começar.

## Conteúdo

| Caminho | Descrição |
|---|---|
| `dados/calendario_letivo_2026.csv` | Calendário oficial (fonte dos dias letivos) |
| `dados/rede_a/rede_a_dump.sql` | Rede A — dump PostgreSQL 16 (schema `educacao`) |
| `dados/rede_b/alunos_rede_b.ndjson` | Rede B — exportação NoSQL, um documento JSON por linha |
| `dados/rede_c/*.csv` | Rede C — 12 planilhas (4 escolas × 3 meses) |

## Restaurar a Rede A

```bash
createdb rede_a
psql -d rede_a -f dados/rede_a/rede_a_dump.sql
```

Com Docker:

```bash
docker run -d --name rede_a -e POSTGRES_PASSWORD=desafio -p 5432:5432 postgres:16
docker exec -i rede_a createdb -U postgres rede_a
docker exec -i rede_a psql -U postgres -d rede_a < dados/rede_a/rede_a_dump.sql
```

## Lembretes

- Período de apuração: 03/08/2026 a 30/10/2026.
- Prazo: 7 dias corridos a partir do recebimento.
- Os arquivos de `resultados/` devem seguir exatamente o layout da seção 6 do enunciado.
- Todos os dados são fictícios.
