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
		af_te_koppelen_oppervlak,
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
		type_gebied,
		geom
FROM 	kadastraal_perceel_subdivided
;


