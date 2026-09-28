
1. Se utilizaran Bloques Horarios de acuerdo a las licitaciones reguladas:
   A: 00:00 - 07:59 | 23:00 - 23:59
   B: 08:00 - 17:59
   C: 18:00 - 22:59
2. La hora extra considerada en el mes de abril sera asociada al Bloque A.
3. La hora faltante de Septiembre no sera considerada en el codigo.
4. Las horas que no tengan medicion sera rellenada con cero.
5. La base de datos de contratos tendra como energia el máxima anual.
6. La base de datos de contratos solo mantendra contratos vigentes.
7. La base de datos de contratos no considera años aislados de energia tranzada.
8. La unidad de medida de contratos es de GWh.
9. Los contratos sin datos de energia quedan en cero.
10. Las medidas de retiros e inyecciones se trabajan en valor absoluto, la convencion de signos queda a interpretacion del usuario.
11. Los datos tendran granularidad horaria.
12. La medida para inyecciones y retiros considerada valida sera la "medida_3".
13. Para la valorizacion de inyecciones y retiros al CMg, se realizara la valorizacion en quinceminutal (PxQ) y se sumaran los registros correspondientes a la hora.
14. La transformacion de CMg quinceminutal a horario sera considerando el promedio de los registros correspondientes a la hora.
15. La transformacion de medicion de consumos e inyecciones de quinceminutal a horario sera considerando la suma de los registros correspondientes a la hora.
16. Los dias tendran una etiqueta de dia habil y no habil considerando el calendario proporcionado por Python.
17. Se guardaran los datos quinceminutales procesados en formato .parquet.
18. Las estadisticas horarias guardadas seran: Promedio, desviacion estandar, maximo y minimo.
19. Cada medicion, tanto de CMg como de inyecciones y retiros tendra como ID el registro quinceminutal mensual.
