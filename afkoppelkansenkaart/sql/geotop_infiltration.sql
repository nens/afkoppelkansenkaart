-- BODEM SCORES TOEVOEGEN AAN PERCELEN OP BASIS VAN GeoTOP CLASSIFICATIES (https://www.dinoloket.nl/sites/default/files/file/TNO_2012_R10991_GeoTOP_modellering_v1.0.pdf)
/* 
Nodig voor dit script:
	- tabel "geotop" met de volgende kolommen: 
		id (= perceel id), 
		geotop_0cm_majority, 
		geotop_50cm_majority, 
		geotop_100cm_majority, 
		geotop_150cm_majority, 
		geotop_200cm_majority, 
		geotop_250cm_majority, 
		geotop_300cm_majority, 
		geotop_350cm_majority, 
		geotop_400cm_majority, 
		geotop_450cm_majority,
		geotop_500cm_majority,
	- kolom ghg_tov_maaiveld van percelen moet ingevuld zijn
*/

DROP TABLE IF EXISTS geotop_score_vertaaltabel;
CREATE TABLE geotop_score_vertaaltabel (
	id integer PRIMARY KEY, 
	geotop_waarde integer UNIQUE NOT NULL,
	score integer
);

INSERT INTO geotop_score_vertaaltabel (geotop_waarde, score) VALUES
	(0, 2),
	(1, 0),
	(2, 0),
	(3, 1),
	(4, 1),
	(5, 2),
	(6, 2),
	(7, 2),
	(8, 2),
	(9, 2)
;

DROP TABLE IF EXISTS perceel_bodem_scores;
CREATE TABLE perceel_bodem_scores AS
	SELECT 	perceel.id,
			vert_0cm AS bodem_score_0cm,
			vert_50cm AS bodem_score_50cm,
			vert_100cm AS bodem_score_100cm,
			vert_150cm AS bodem_score_150cm,
			vert_200cm AS bodem_score_200cm,
			vert_250cm AS bodem_score_250cm,
			vert_300cm AS bodem_score_300cm,
			vert_350cm AS bodem_score_350cm,
			vert_400cm AS bodem_score_400cm,
			vert_450cm AS bodem_score_450cm,
			vert_500cm AS bodem_score_500cm			
	from 	kadastraal_perceel_subdivided AS perceel
	left join geotop 
		on 	geotop.id = perceel.id
	left join geotop_score_vertaaltabel AS vert_0cm
		ON 	geotop.geotop_0cm_majority = vert_0cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_50cm
		ON 	geotop.geotop_50cm_majority = vert_50cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_100cm
		ON 	geotop.geotop_100cm_majority = vert_100cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_150cm
		ON 	geotop.geotop_150cm_majority = vert_150cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_200cm
		ON 	geotop.geotop_200cm_majority = vert_200cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_250cm
		ON 	geotop.geotop_250cm_majority = vert_250cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_300cm
		ON 	geotop.geotop_300cm_majority = vert_300cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_350cm
		ON 	geotop.geotop_350cm_majority = vert_350cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_400cm
		ON 	geotop.geotop_400cm_majority = vert_400cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_450cm
		ON 	geotop.geotop_450cm_majority = vert_450cm.geotop_waarde
	left join geotop_score_vertaaltabel AS vert_500cm
		ON 	geotop.geotop_500cm_majority = vert_500cm.geotop_waarde
;


-- BEREKENEN TOTALE GeoTOP SCORE PER PERCEEL OP BASIS VAN ALLE LAGEN
ALTER TABLE perceel_bodem_scores ADD COLUMN bodem_score_geotop double precision;
-- INSERT INTO work.percelen_woonkernen_gem_zevenaar_final(ghg_min) SELECT ghg_min FROM owners;

--Weegfactoren: w1 = 2, w2 = 2, w3 = 1.5
--Factor laagdikte: z1 = 0.5 , z2 = (ghg_min - laagste meting boven grondwater)

-- Weegfactoren voor verticale positionering van de laag en de dikte van een bodemlaag
with weegfactoren as ( 
	select 	2 as w1, 
			2 as w2, 
			1.5 as w3, 
			0.5 as z1
)
update 	kadastraal_perceel_subdivided AS tgt
set 	geschiktheid_infiltratie = 
	case
		when tgt.ghg_tov_maaiveld <= 0 then 0
		when tgt.ghg_tov_maaiveld > 0 and tgt.ghg_tov_maaiveld <= 0.5 then bodem_score_0cm
		when tgt.ghg_tov_maaiveld >= 0.5 and tgt.ghg_tov_maaiveld <= 1.0 then ( wf.w1 * wf.z1 * bodem_score_0cm + wf.w2 * (ghg_mv_median - 0.5) * bodem_score_50cm ) / ( wf.w1 * wf.z1 + wf.w2 * (ghg_mv_median - 0.5) )
		when tgt.ghg_tov_maaiveld >= 1.0 and tgt.ghg_tov_maaiveld <= 1.5 then ( wf.w1 * wf.z1 * bodem_score_0cm + wf.w2 * wf.z1 * bodem_score_50cm + wf.w3 * (ghg_mv_median - 1.0) * bodem_score_100cm ) / ( wf.w1 * wf.z1 + wf.w2 * wf.z1 + wf.w3 * (ghg_mv_median - 1.0) )
		when tgt.ghg_tov_maaiveld >= 1.5 and tgt.ghg_tov_maaiveld <= 2.0 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm ) * wf.z1 + (ghg_mv_median - 1.5) * bodem_score_150cm ) / ( (wf.w1 + wf.w2 + wf.w3) * wf.z1 + (ghg_mv_median - 1.5) )
		when tgt.ghg_tov_maaiveld >= 2.0 and tgt.ghg_tov_maaiveld <= 2.5 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm + bodem_score_150cm ) * wf.z1 + (ghg_mv_median - 2.0) * bodem_score_200cm ) / ( (wf.w1 + wf.w2 + wf.w3 + 1) * wf.z1 + (ghg_mv_median - 2.0) )
		when tgt.ghg_tov_maaiveld >= 2.5 and tgt.ghg_tov_maaiveld <= 3.0 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm + bodem_score_150cm + bodem_score_200cm ) * wf.z1 + (ghg_mv_median - 2.5) * bodem_score_250cm ) / ( (wf.w1 + wf.w2 + wf.w3 + 2) * wf.z1 + (ghg_mv_median - 2.5) )
		when tgt.ghg_tov_maaiveld >= 3.0 and tgt.ghg_tov_maaiveld <= 3.5 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm + bodem_score_150cm + bodem_score_200cm + bodem_score_250cm ) * wf.z1 + (ghg_mv_median - 3.0) * bodem_score_300cm ) / ( (wf.w1 + wf.w2 + wf.w3 + 3) * wf.z1 + (ghg_mv_median - 3.0) )
		when tgt.ghg_tov_maaiveld >= 3.5 and tgt.ghg_tov_maaiveld <= 4.0 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm + bodem_score_150cm + bodem_score_200cm + bodem_score_250cm + bodem_score_300cm ) * wf.z1 + (ghg_mv_median - 3.5) * bodem_score_350cm ) / ( (wf.w1 + wf.w2 + wf.w3 + 4) * wf.z1 + (ghg_mv_median - 3.5) )
		when tgt.ghg_tov_maaiveld >= 4.0 and tgt.ghg_tov_maaiveld <= 4.5 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm + bodem_score_150cm + bodem_score_200cm + bodem_score_250cm + bodem_score_300cm + bodem_score_350cm) * wf.z1 + (ghg_mv_median - 4.0) * bodem_score_400cm ) / ( (wf.w1 + wf.w2 + wf.w3 + 5) * wf.z1 + (ghg_mv_median - 4.0) )	
		when tgt.ghg_tov_maaiveld >= 4.5 and tgt.ghg_tov_maaiveld <= 5.0 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm + bodem_score_150cm + bodem_score_200cm + bodem_score_250cm + bodem_score_300cm + bodem_score_350cm + bodem_score_400cm) * wf.z1 + (ghg_mv_median - 4.5) * bodem_score_450cm ) / ( (wf.w1 + wf.w2 + wf.w3 + 6) * wf.z1 + (ghg_mv_median - 4.5) )
		when tgt.ghg_tov_maaiveld >= 5.0 and tgt.ghg_tov_maaiveld <= 6.5 then ( ( wf.w1 * bodem_score_0cm + wf.w2 * bodem_score_50cm + wf.w3 * bodem_score_100cm + bodem_score_150cm + bodem_score_200cm + bodem_score_250cm + bodem_score_300cm + bodem_score_350cm + bodem_score_400cm + bodem_score_450cm) * wf.z1 + (ghg_mv_median - 5.0) * bodem_score_500cm ) / ( (wf.w1 + wf.w2 + wf.w3 + 7) * wf.z1 + (ghg_mv_median - 5.0) )	
	end
from 	weegfactoren AS wf,
		perceel_bodem_scores AS bod
where 	tgt.id = bod.id
;
