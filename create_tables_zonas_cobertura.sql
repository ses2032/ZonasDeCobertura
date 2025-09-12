-- =============================================
-- Script SQL Server para Sistema de Zonas de Cobertura
-- Basado en los modelos C# definidos en API_DOCUMENTATION.md
-- =============================================

-- Crear base de datos si no existe (opcional)
-- CREATE DATABASE ZonasCobertura;
-- GO
-- USE ZonasCobertura;
-- GO

-- =============================================
-- Tabla: ZonasCobertura
-- Corresponde al modelo C# ZonaCobertura
-- =============================================
CREATE TABLE ZonasCobertura (
    ZonaId INT IDENTITY(1,1) NOT NULL,
    SucursalId INT NOT NULL,
    NombreZona NVARCHAR(255) NOT NULL,
    FechaCreacion DATETIME2(7) NOT NULL DEFAULT GETUTCDATE(),
    Activa BIT NOT NULL DEFAULT 1,
    CONSTRAINT PK_ZonasCobertura PRIMARY KEY (ZonaId)
);
GO

-- =============================================
-- Tabla: CoordenadasZona
-- Corresponde al modelo C# Coordenada
-- Almacena las coordenadas del polígono de cada zona
-- =============================================
CREATE TABLE CoordenadasZona (
    CoordenadaId INT IDENTITY(1,1) NOT NULL,
    ZonaId INT NOT NULL,
    Latitud DECIMAL(18, 8) NOT NULL,
    Longitud DECIMAL(18, 8) NOT NULL,
    Orden INT NOT NULL, -- Para mantener el orden de los puntos del polígono
    CONSTRAINT PK_CoordenadasZona PRIMARY KEY (CoordenadaId)
);
GO

-- =============================================
-- Tabla: CallesCobertura
-- Corresponde al modelo C# CalleCobertura
-- Almacena las calles incluidas en cada zona de cobertura
-- =============================================
CREATE TABLE CallesCobertura (
    CalleId INT IDENTITY(1,1) NOT NULL,
    ZonaId INT NOT NULL,
    NombreCalle NVARCHAR(255) NOT NULL,
    AlturaDesde INT NOT NULL,
    AlturaHasta INT NOT NULL,
    CONSTRAINT PK_CallesCobertura PRIMARY KEY (CalleId)
);
GO

-- =============================================
-- ÍNDICES PARA OPTIMIZACIÓN DE RENDIMIENTO
-- =============================================

-- Índice para búsquedas por SucursalId en ZonasCobertura
CREATE NONCLUSTERED INDEX IX_ZonasCobertura_SucursalId 
ON ZonasCobertura (SucursalId);
GO

-- Índice para búsquedas por zona activa
CREATE NONCLUSTERED INDEX IX_ZonasCobertura_Activa 
ON ZonasCobertura (Activa);
GO

-- Índice compuesto para búsquedas por sucursal y estado activo
CREATE NONCLUSTERED INDEX IX_ZonasCobertura_SucursalId_Activa 
ON ZonasCobertura (SucursalId, Activa);
GO

-- Índice para búsquedas por ZonaId en CoordenadasZona
CREATE NONCLUSTERED INDEX IX_CoordenadasZona_ZonaId 
ON CoordenadasZona (ZonaId);
GO

-- Índice para búsquedas por ZonaId en CallesCobertura
CREATE NONCLUSTERED INDEX IX_CallesCobertura_ZonaId 
ON CallesCobertura (ZonaId);
GO

-- Índice para búsquedas por nombre de calle
CREATE NONCLUSTERED INDEX IX_CallesCobertura_NombreCalle 
ON CallesCobertura (NombreCalle);
GO

-- =============================================
-- RESTRICCIONES DE INTEGRIDAD REFERENCIAL
-- =============================================

-- Foreign Key: CoordenadasZona -> ZonasCobertura
ALTER TABLE CoordenadasZona
ADD CONSTRAINT FK_CoordenadasZona_ZonasCobertura 
FOREIGN KEY (ZonaId) REFERENCES ZonasCobertura(ZonaId) 
ON DELETE CASCADE;
GO

-- Foreign Key: CallesCobertura -> ZonasCobertura
ALTER TABLE CallesCobertura
ADD CONSTRAINT FK_CallesCobertura_ZonasCobertura 
FOREIGN KEY (ZonaId) REFERENCES ZonasCobertura(ZonaId) 
ON DELETE CASCADE;
GO

-- =============================================
-- RESTRICCIONES DE VALIDACIÓN (CHECK CONSTRAINTS)
-- =============================================

-- Validar que las coordenadas estén en rangos válidos
ALTER TABLE CoordenadasZona
ADD CONSTRAINT CK_CoordenadasZona_Latitud 
CHECK (Latitud >= -90 AND Latitud <= 90);
GO

ALTER TABLE CoordenadasZona
ADD CONSTRAINT CK_CoordenadasZona_Longitud 
CHECK (Longitud >= -180 AND Longitud <= 180);
GO

-- Validar que las alturas de las calles sean positivas y lógicas
ALTER TABLE CallesCobertura
ADD CONSTRAINT CK_CallesCobertura_AlturaDesde 
CHECK (AlturaDesde >= 0);
GO

ALTER TABLE CallesCobertura
ADD CONSTRAINT CK_CallesCobertura_AlturaHasta 
CHECK (AlturaHasta >= 0);
GO

-- Validar que AlturaHasta sea mayor o igual a AlturaDesde
ALTER TABLE CallesCobertura
ADD CONSTRAINT CK_CallesCobertura_Alturas_Logicas 
CHECK (AlturaHasta >= AlturaDesde);
GO

-- Validar que el orden de las coordenadas sea positivo
ALTER TABLE CoordenadasZona
ADD CONSTRAINT CK_CoordenadasZona_Orden 
CHECK (Orden > 0);
GO

-- =============================================
-- COMENTARIOS EN TABLAS Y COLUMNAS
-- =============================================

-- Comentarios para la tabla ZonasCobertura
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Tabla principal que almacena las zonas de cobertura de delivery por sucursal', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'ZonasCobertura';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Identificador único de la zona de cobertura', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'ZonasCobertura', 
    @level2type = N'COLUMN', @level2name = N'ZonaId';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Identificador de la sucursal a la que pertenece la zona', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'ZonasCobertura', 
    @level2type = N'COLUMN', @level2name = N'SucursalId';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Nombre descriptivo de la zona de cobertura', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'ZonasCobertura', 
    @level2type = N'COLUMN', @level2name = N'NombreZona';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Fecha y hora de creación de la zona en UTC', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'ZonasCobertura', 
    @level2type = N'COLUMN', @level2name = N'FechaCreacion';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Indica si la zona está activa (1) o inactiva (0)', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'ZonasCobertura', 
    @level2type = N'COLUMN', @level2name = N'Activa';
GO

-- Comentarios para la tabla CoordenadasZona
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Tabla que almacena las coordenadas que forman el polígono de cada zona de cobertura', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CoordenadasZona';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Identificador único de la coordenada', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CoordenadasZona', 
    @level2type = N'COLUMN', @level2name = N'CoordenadaId';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Latitud de la coordenada en formato decimal', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CoordenadasZona', 
    @level2type = N'COLUMN', @level2name = N'Latitud';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Longitud de la coordenada en formato decimal', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CoordenadasZona', 
    @level2type = N'COLUMN', @level2name = N'Longitud';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Orden secuencial del punto en el polígono de la zona', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CoordenadasZona', 
    @level2type = N'COLUMN', @level2name = N'Orden';
GO

-- Comentarios para la tabla CallesCobertura
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Tabla que almacena las calles incluidas en cada zona de cobertura con sus rangos de altura', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CallesCobertura';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Identificador único de la calle en la zona', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CallesCobertura', 
    @level2type = N'COLUMN', @level2name = N'CalleId';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Nombre de la calle incluida en la zona de cobertura', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CallesCobertura', 
    @level2type = N'COLUMN', @level2name = N'NombreCalle';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Altura mínima de la calle incluida en la zona', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CallesCobertura', 
    @level2type = N'COLUMN', @level2name = N'AlturaDesde';
GO

EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'Altura máxima de la calle incluida en la zona', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'CallesCobertura', 
    @level2type = N'COLUMN', @level2name = N'AlturaHasta';
GO

-- =============================================
-- DATOS DE EJEMPLO (OPCIONAL)
-- =============================================

-- Insertar datos de ejemplo para testing
INSERT INTO ZonasCobertura (SucursalId, NombreZona, Activa)
VALUES 
    (1, 'Zona Centro', 1),
    (1, 'Zona Norte', 1),
    (2, 'Zona Sur', 1);
GO

-- Insertar coordenadas de ejemplo para la Zona Centro (ZonaId = 1)
INSERT INTO CoordenadasZona (ZonaId, Latitud, Longitud, Orden)
VALUES 
    (1, -38.7163706, -62.2618418, 1),
    (1, -38.7200000, -62.2600000, 2),
    (1, -38.7150000, -62.2650000, 3),
    (1, -38.7163706, -62.2618418, 4); -- Cerrar el polígono
GO

-- Insertar calles de ejemplo para la Zona Centro (ZonaId = 1)
INSERT INTO CallesCobertura (ZonaId, NombreCalle, AlturaDesde, AlturaHasta)
VALUES 
    (1, 'LAMADRID', 100, 500),
    (1, 'SAN MARTIN', 200, 800);
GO

-- =============================================
-- VISTAS ÚTILES PARA CONSULTAS
-- =============================================

-- Vista para obtener zonas con sus coordenadas como JSON
CREATE VIEW vw_ZonasCoberturaCompletas AS
SELECT 
    z.ZonaId,
    z.SucursalId,
    z.NombreZona,
    z.FechaCreacion,
    z.Activa,
    (
        SELECT 
            c.Latitud,
            c.Longitud
        FROM CoordenadasZona c
        WHERE c.ZonaId = z.ZonaId
        ORDER BY c.Orden
        FOR JSON PATH
    ) AS PoligonoCoordenadas,
    (
        SELECT 
            cal.CalleId,
            cal.NombreCalle,
            cal.AlturaDesde,
            cal.AlturaHasta
        FROM CallesCobertura cal
        WHERE cal.ZonaId = z.ZonaId
        FOR JSON PATH
    ) AS Calles
FROM ZonasCobertura z;
GO

-- Vista para obtener estadísticas de zonas por sucursal
CREATE VIEW vw_EstadisticasZonasPorSucursal AS
SELECT 
    z.SucursalId,
    COUNT(*) AS TotalZonas,
    SUM(CASE WHEN z.Activa = 1 THEN 1 ELSE 0 END) AS ZonasActivas,
    SUM(CASE WHEN z.Activa = 0 THEN 1 ELSE 0 END) AS ZonasInactivas,
    COUNT(DISTINCT c.CalleId) AS TotalCalles,
    COUNT(DISTINCT co.CoordenadaId) AS TotalCoordenadas
FROM ZonasCobertura z
LEFT JOIN CallesCobertura c ON z.ZonaId = c.ZonaId
LEFT JOIN CoordenadasZona co ON z.ZonaId = co.ZonaId
GROUP BY z.SucursalId;
GO

-- =============================================
-- PROCEDIMIENTOS ALMACENADOS ÚTILES
-- =============================================

-- Procedimiento para obtener zonas de cobertura por sucursal
CREATE PROCEDURE sp_GetZonasCoberturaBySucursal
    @SucursalId INT
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        z.ZonaId,
        z.SucursalId,
        z.NombreZona,
        z.FechaCreacion,
        z.Activa,
        (
            SELECT 
                c.Latitud,
                c.Longitud
            FROM CoordenadasZona c
            WHERE c.ZonaId = z.ZonaId
            ORDER BY c.Orden
            FOR JSON PATH
        ) AS PoligonoCoordenadas,
        (
            SELECT 
                cal.CalleId,
                cal.NombreCalle,
                cal.AlturaDesde,
                cal.AlturaHasta
            FROM CallesCobertura cal
            WHERE cal.ZonaId = z.ZonaId
            FOR JSON PATH
        ) AS Calles
    FROM ZonasCobertura z
    WHERE z.SucursalId = @SucursalId
    AND z.Activa = 1
    ORDER BY z.NombreZona;
END;
GO

-- Procedimiento para guardar una nueva zona de cobertura
CREATE PROCEDURE sp_GuardarZonaCobertura
    @SucursalId INT,
    @NombreZona NVARCHAR(255),
    @Activa BIT = 1,
    @ZonaId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Insertar la zona
        INSERT INTO ZonasCobertura (SucursalId, NombreZona, Activa)
        VALUES (@SucursalId, @NombreZona, @Activa);
        
        SET @ZonaId = SCOPE_IDENTITY();
        
        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END;
GO

-- =============================================
-- SCRIPT COMPLETADO
-- =============================================

PRINT 'Script de creación de tablas para Sistema de Zonas de Cobertura completado exitosamente.';
PRINT 'Tablas creadas:';
PRINT '- ZonasCobertura (tabla principal)';
PRINT '- CoordenadasZona (coordenadas del polígono)';
PRINT '- CallesCobertura (calles incluidas en la zona)';
PRINT 'Índices, restricciones y procedimientos almacenados incluidos.';

