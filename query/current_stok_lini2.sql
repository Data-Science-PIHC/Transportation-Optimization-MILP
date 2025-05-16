SELECT DISTINCT
                STOK.DATE_SENT AS TANGGAL,
                "Nama Gudang" AS GUDANG,
                STOK.PLANT AS "KODE PLANT",
                tipe.KATEGORI_PRODUK AS "PRODUK",
                CASE LEFT(UPPER(STOK.PLANT), 1)
                    WHEN 'A' THEN 'PI'
                    WHEN 'B' THEN 'PKG'
                    WHEN 'C' THEN 'PKC'
                    WHEN 'D' THEN 'PKT'
                    WHEN 'E' THEN 'PIM'
                    WHEN 'F' THEN 'PSP'
                    ELSE 'LAINNYA'
                END AS PRODUSEN,
                "Kap Gudang (ton)" AS "KAPASITAS",
                UPPER("Provinsi") AS "PROVINSI", 
                UPPER("Kabupaten") AS "KABUPATEN",
                SUM(UU) + SUM(Q_TRANS) AS "STOK FISIK",
                SUM(Q_TRANS) AS INTRANSIT
            FROM 
            (
                SELECT 
                    MAX(DATE_SENT) AS DATE_SENT,
                    PLANT,
                    MAT_DESC
                FROM REKOMENDASI_STOK.PUBLIC.STOK
                GROUP BY 2,3
            ) stok_filtered 
                LEFT JOIN REKOMENDASI_STOK.PUBLIC.STOK
                    ON stok_filtered.DATE_SENT = STOK.DATE_SENT 
                    AND stok_filtered.PLANT = STOK.PLANT
                    AND stok_filtered.MAT_DESC = STOK.MAT_DESC
            INNER JOIN REKOMENDASI_STOK.PUBLIC.ALL_PLANT prioritas ON prioritas."KODE PLANT" = stok.PLANT
            INNER JOIN OPTIMIZATION_TRANSPORTATION.PUBLIC.PUPUK_AKTIF tipe ON stok.PRODUK = tipe.ID_MATERIAL
            LEFT JOIN REKOMENDASI_STOK.PUBLIC.MASTER_PLANT_VERSI_DISTRIBUSI dist ON dist."Kode Plant" = stok.PLANT
            WHERE TANGGAL = DATE(TIMEADD(HOUR, +14, CURRENT_TIMESTAMP))
            AND "KODE PLANT" IN ({warehouse_codes})
            GROUP BY 1,2,3,4,5,6,7,8
            ORDER BY GUDANG ASC, TANGGAL DESC
