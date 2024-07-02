def test_quantity_1():
    from hg_oap.units.default_unit_system import U

    with U:
        assert 1.0 * U.m == 1.0 * U.m
        assert 1.0 * U.m == 100.0 * U.cm

        assert 60.0 * U.s == 1.0 * U.min

        assert 1.0 * U.kWh == 3600000.0 * U.J

        assert 1.25 * (1.0 / U.K) == 1.25 * (1.0 / U.degC.diff)

        assert 2.0 * (U.km / U.h) - 0.556 * (U.m / U.s) < 0.001 * (U.m / U.s)

        assert 100.0 * U.g + 1.0 * U.kg == 1100.0 * U.g
        assert 1.0 * U.m + 1.0 * U.cm == 101.0 * U.cm

        assert 1.0 * U.m**2 == 10000.0 * U.cm**2
        assert 1.0 * U.m * (1.0 * U.m) == 1.0 * U.m**2

        assert 1.0 * U.m**3 < 1000.1 * U.l
        assert 1.0 * U.m**3 >= 1000.0 * U.l
        assert 1.0 * U.m**3 > 999.99 * U.l
        assert 1.0 * U.m**3 <= 1000.0 * U.l

        assert (1.0 * U.m) ** 3 == 1000.0 * U.l

        assert 2.0 * U.rpm == (1 / 30.0) * U.s**-1
