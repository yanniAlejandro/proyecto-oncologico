export function HospitalLogo({ size = 52 }: { size?: number }) {
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
