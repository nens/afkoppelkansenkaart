-- The views defined below depend on a view perceel_criteriumwaarde, which is dynamically created in a python function based on
-- the contents of the table 'criterium'. So first run schema_tables.sql, initialisation.sql, and
-- create_perceel_criteriumwaarde_view() before running the sql below

CREATE VIEW IF NOT EXISTS perceel_criteriumscore AS
SELECT  row_number() over() as id,
        waarde.perceel_id,
        waarde.criterium_id,
        coalesce (klasse.score, categorie.score) AS score
FROM    perceel_criteriumwaarde AS waarde
LEFT JOIN score_zoektabel AS klasse
    ON  waarde.criterium_id = klasse.criterium_id
        AND CAST(waarde.waarde AS real) > klasse.klasse_ondergrens
        AND CAST(waarde.waarde AS real) <= klasse.klasse_bovengrens
LEFT JOIN score_zoektabel AS categorie
    ON  waarde.criterium_id = categorie.criterium_id
        AND waarde.waarde = categorie.code
;

CREATE VIEW IF NOT EXISTS perceel_domeinscore AS
SELECT  row_number() over() as id,
        pcs.perceel_id,
        domein.id AS domein_id,
        sum(pcs.score * weging.factor) / sum(weging.factor) AS score
FROM    perceel_criteriumscore AS pcs
LEFT JOIN criterium
    ON  pcs.criterium_id = criterium.id
LEFT JOIN domein
    ON  criterium.domein_id = domein.id
LEFT JOIN weging
    ON  score_type = 'criterium'
        AND score_id = criterium.id
GROUP BY pcs.perceel_id, domein.id
;

CREATE VIEW IF NOT EXISTS perceel_hoofdonderdeelscore AS
SELECT  row_number() over() as id,
        pds.perceel_id,
        hoofdonderdeel.id AS hoofdonderdeel_id,
        sum(pds.score * weging.factor) / sum(weging.factor) AS score
FROM    perceel_domeinscore AS pds
LEFT JOIN domein
    ON  pds.domein_id = domein.id
LEFT JOIN hoofdonderdeel
    ON  domein.hoofdonderdeel_id = hoofdonderdeel.id
LEFT JOIN weging
    ON  score_type = 'domein'
        AND score_id = domein.id
GROUP BY pds.perceel_id, hoofdonderdeel.id
;

CREATE VIEW IF NOT EXISTS perceel_eindscore AS
SELECT  phs.perceel_id,
        sum(phs.score * weging.factor) / sum(weging.factor) AS score
FROM    perceel_hoofdonderdeelscore AS phs
LEFT JOIN hoofdonderdeel
    ON  phs.hoofdonderdeel_id = hoofdonderdeel.id
LEFT JOIN weging
    ON  score_type = 'hoofdonderdeel'
        AND score_id = hoofdonderdeel.id
GROUP BY phs.perceel_id
;

CREATE VIEW IF NOT EXISTS buurt_eindscore AS
SELECT  buurt.*,
        ROUND(SUM(ST_Area(perceel.geom) * eind.score) / SUM(ST_Area(perceel.geom)), 3) as gemiddelde_eindscore
FROM    buurt
LEFT JOIN perceel
    ON  ST_Intersects(perceel.geom, buurt.geom)
JOIN    perceel_eindscore AS eind
    ON  perceel.id = eind.perceel_id
GROUP BY buurt.naam
;

CREATE VIEW IF NOT EXISTS wijk_eindscore AS
SELECT  wijk.*,
        ROUND(SUM(ST_Area(perceel.geom) * eind.score) / SUM(ST_Area(perceel.geom)), 3) as gemiddelde_eindscore
FROM    wijk
LEFT JOIN perceel
    ON  ST_Intersects(perceel.geom, wijk.geom)
JOIN    perceel_eindscore AS eind
    ON  perceel.id = eind.perceel_id
GROUP BY wijk.naam
;
