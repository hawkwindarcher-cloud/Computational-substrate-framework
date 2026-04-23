import math
import random
from typing import Dict, List

# ============================================================
# GLOBAL LIGHT DEFINITIONS
# ============================================================

LIGHT_WAVELENGTHS = {
    "red": 680,
    "blue": 430,
    "green": 550,
    "far_red": 730
}

WHITE_SPECTRUM = [430, 480, 550, 620, 680]  # representative sampling

# ============================================================
# CODECS
# ============================================================

class Codec2:
    def vector_absorption(self, freq_thz: float, absorption_cross_section: float = 1.0):
        if freq_thz <= 0:
            return {"absorbed": False, "energy_ev": 0}

        energy_ev = freq_thz * 4.136e-3
        prob = min(1.0, absorption_cross_section * freq_thz / 1000)

        if random.random() < prob:
            return {"absorbed": True, "energy_ev": energy_ev, "probability": prob}

        return {"absorbed": False, "energy_ev": 0, "probability": prob}


class Codec6:
    def identity_rewrite(self, info_budget, required_info, alternatives):
        if info_budget >= required_info:
            return {"rewritten": False}

        viable = [a for a in alternatives if a["required_info"] <= required_info * 2]
        if not viable:
            return {"rewritten": False}

        return {"rewritten": True, "mode": random.choice(viable)["type"]}


# ============================================================
# MOLECULES
# ============================================================

class ChlorophyllMolecule:
    def __init__(self):
        self.codec2 = Codec2()
        self.absorption_peaks = [430, 680]

    def photon_absorption(self, wavelength_nm):
        freq_thz = 300000 / wavelength_nm
        efficiency = max(
            0.1,
            1.0 - min(abs(wavelength_nm - p) / 100 for p in self.absorption_peaks)
        )
        return self.codec2.vector_absorption(freq_thz, efficiency)

    def photon_absorption_white(self):
        total_energy = 0
        absorbed_any = False

        for wl in WHITE_SPECTRUM:
            result = self.photon_absorption(wl)
            if result["absorbed"]:
                absorbed_any = True
                total_energy += result["energy_ev"]

        return {
            "absorbed": absorbed_any,
            "energy_ev": total_energy
        }


# ============================================================
# PHOTOSYSTEMS
# ============================================================

class PhotosystemII:
    def __init__(self):
        self.chl = ChlorophyllMolecule()
        self.codec6 = Codec6()

    def water_oxidation(self, photon_flux):
        if photon_flux.get("broadband"):
            absorb = self.chl.photon_absorption_white()
        else:
            absorb = self.chl.photon_absorption(photon_flux["wavelength"])
        
        if not absorb["absorbed"]:
            return {"success": False}

        rewrite = self.codec6.identity_rewrite(0.5, 0.6, [
            {"type": "oxidation", "required_info": 0.4}
        ])

        if rewrite["rewritten"]:
            return {
                "success": True,
                "electrons": 4,
                "oxygen": 1,
                "protons": 4
            }

        return {"success": False}


class ElectronTransportChain:
    def transport(self, electrons):
        if electrons <= 0:
            return {"success": False}

        protons = electrons * 2
        atp_potential = max(1, protons // 3)

        return {
            "success": True,
            "protons": protons,
            "atp_potential": atp_potential
        }


class PhotosystemI:
    def __init__(self):
        self.chl = ChlorophyllMolecule()
        self.codec6 = Codec6()

    def nadph_reduction(self, photon_flux, electrons):
        if electrons <= 0:
            return {"success": False}

        if photon_flux.get("broadband"):
            absorb = self.chl.photon_absorption_white()
        else:
            absorb = self.chl.photon_absorption(photon_flux["wavelength"])
        
        if not absorb["absorbed"]:
            return {"success": False}

        nadph = max(1, electrons // 2)
        return {"success": True, "nadph": nadph}


class ATPSynthase:
    def synthesize(self, atp_potential):
        return max(0, atp_potential)


class RuBisCO:
    def fix(self, atp_pool, nadph_pool):
        if atp_pool >= 3 and nadph_pool >= 2:
            return {"success": True}
        return {"success": False}


# ============================================================
# CHLOROPLAST
# ============================================================

class Chloroplast:
    def __init__(self):
        self.psii = PhotosystemII()
        self.psi = PhotosystemI()
        self.etc = ElectronTransportChain()
        self.atpase = ATPSynthase()
        self.rubisco = RuBisCO()

        self.atp_pool = 0
        self.nadph_pool = 0

    def environmental_response(self, temperature, co2, light_quality):
        temp_factor = 1.0 if 20 <= temperature <= 30 else 0.6
        co2_factor = min(1.0, co2 / 400)
        quality_factor = {"white": 1.0, "red": 0.8, "blue": 0.7, "green": 0.2}.get(light_quality, 0.5)

        return {
            "factor": temp_factor * co2_factor * quality_factor,
            "wavelength": LIGHT_WAVELENGTHS.get(light_quality, 680),
            "broadband": light_quality == "white"
        }

    def step(self, light_intensity, temperature=25, co2=400, light_quality="white"):
        env = self.environmental_response(temperature, co2, light_quality)

        photon_flux = {
            "intensity": light_intensity * env["factor"],
            "wavelength": env["wavelength"],
            "broadband": env.get("broadband", False)
        }

        psii = self.psii.water_oxidation(photon_flux)
        if not psii["success"]:
            return False

        etc = self.etc.transport(psii["electrons"])
        atp = self.atpase.synthesize(etc["atp_potential"])
        self.atp_pool += atp

        psi = self.psi.nadph_reduction(photon_flux, psii["electrons"])
        if psi["success"]:
            self.nadph_pool += psi["nadph"]

        carbon = self.rubisco.fix(self.atp_pool, self.nadph_pool)
        if carbon["success"]:
            self.atp_pool -= 3
            self.nadph_pool -= 2
            return True

        return False

    def run(self, steps=20, **kwargs):
        successes = 0
        for _ in range(steps):
            if self.step(**kwargs):
                successes += 1
        return successes


# ============================================================
# DEMO
# ============================================================

if __name__ == "__main__":
    chl = Chloroplast()
    successes = chl.run(
        steps=20,
        light_intensity=1.0,
        temperature=25,
        co2=400,
        light_quality="blue"
    )

    print("Photosynthetic steps with glucose:", successes)
    print("Final ATP pool:", chl.atp_pool)
    print("Final NADPH pool:", chl.nadph_pool)
