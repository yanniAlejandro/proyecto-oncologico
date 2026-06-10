interface HospitalLogoProps {
  size?: number;
}

export function HospitalLogo({ size = 52 }: HospitalLogoProps) {
  return (
    <img
      src="/logo-holh.svg"
      alt="Hospital Oncológico de La Habana"
      width={size}
      height={size}
      className="hospital-logo"
    />
  );
}
