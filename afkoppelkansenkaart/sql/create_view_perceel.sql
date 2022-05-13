-- Create view for exporting to Geopackage
DROP VIEW IF EXISTS perceel;
CREATE OR REPLACE VIEW perceel AS 
SELECT	id, 
		brk_lokaalid, 
		brk_perceelnummer, 
		oppervlakte_perceel, 
		gemeentelijk_eigendom, 
		oppervlakte_bebouwing, 
		percentage_bebouwing, 
		verhard_oppervlak, 
		verhard_percentage,
		maaiveldhoogte,
		bodemsoort, 
		doorlatendheid_bodem, 
		ghg_tov_maaiveld, 
		afstand_tot_bergingslocatie, 
		code_dichtsbijzijnde_rioolleiding, 
		type_rioolstelsel, 
		kwetsbaarheid_oppervlaktewater, 
		aantal_keer_verpompen, 
		afstand_tot_rwzi, 
		gebiedstype_wateroverlast,
		geom
FROM 	kadastraal_perceel_subdivided
;


