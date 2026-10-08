// Ghidra headless script used for data/secure/hyp_arb_fuse_reference_check.txt. Image base 0x100000 (hyp.img segment_1).
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
public class arb_fuse_refs_check extends GhidraScript {
  public void run() throws Exception {
    AddressSpace s = currentProgram.getAddressFactory().getDefaultAddressSpace();
    MemoryBlock b = currentProgram.getMemory().getBlock(s.getAddress(0x100000L));
    int n = 0;
    Address a = b.getStart();
    while (a != null && a.compareTo(b.getEnd()) < 0) {
      if (currentProgram.getListing().getInstructionAt(a) == null) {
        if (disassemble(a)) n++;
      }
      a = a.add(4);
    }
    println("disassembled " + n);
    String[] addrs = {"0013eb4c","001260c4","00126000","00126060","0013eb6c","00126024","00126088"};
    for (String h : addrs) {
      Address t = s.getAddress(Long.parseLong(h,16));
      ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(t);
      int c=0; StringBuilder sb=new StringBuilder();
      while (it.hasNext()) { Reference r=it.next(); c++; sb.append(" "+r.getFromAddress()+"/"+r.getReferenceType()); }
      println("refs to " + h + " count " + c + sb);
    }
  }
}
