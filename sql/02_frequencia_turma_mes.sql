SELECT
    rede,
    inep_escola,
    nome_escola,
    codigo_turma,
    serie,
    mes_referencia,
    SUM(is_presente) AS total_presencas,
    COUNT(1) AS total_registros_validos,
    ROUND((SUM(is_presente) / COUNT(1)) * 100, 2) AS pct_frequencia
FROM 
    `motriz-desafio.educacao_stg.stg_frequencia_validos`
GROUP BY
    rede, inep_escola, nome_escola, codigo_turma, serie, mes_referencia
ORDER BY
    rede, codigo_turma, mes_referencia;