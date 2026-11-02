#include <cstdio>
#include <cstdlib>
#include <vector>
#include <fstream>
#include <filesystem>
#include <unistd.h>
#include "gpupixel/gpupixel.h"
int main(int argc, char** argv) {
  if(argc!=7){fprintf(stderr,"usage: gpupixel_stream width height blur white sharpen resource_root\n"); return 2;}
  int w=atoi(argv[1]), h=atoi(argv[2]);
  if(w<=0||h<=0||w>16384||h>16384){fprintf(stderr,"invalid frame size\n");return 2;}
  for(const char* name:{"lookup_gray.png","lookup_origin.png","lookup_skin.png","lookup_light.png"}){
    auto path=std::filesystem::path(argv[6])/"res"/name;
    std::ifstream resource(path,std::ios::binary);
    char first;
    if(!resource.get(first)){fprintf(stderr,"missing or unreadable GPUPixel resource: %s\n",path.string().c_str());return 9;}
  }
  FILE* out=fdopen(dup(STDOUT_FILENO),"wb");
  if(!out)return 3;
  dup2(STDERR_FILENO,STDOUT_FILENO);
  gpupixel::GPUPixel::SetResourcePath(argv[6]);
  auto source=gpupixel::SourceRawData::Create();
  auto beauty=gpupixel::BeautyFaceFilter::Create();
  auto sink=gpupixel::SinkRawData::Create();
  if(!source||!beauty||!sink)return 3;
  beauty->SetBlurAlpha(atof(argv[3]));
  beauty->SetWhite(atof(argv[4]));
  beauty->SetSharpen(atof(argv[5]));
  source->AddSink(beauty); beauty->AddSink(sink);
  std::vector<uint8_t> frame(size_t(w)*h*4);
  int count=0;
  size_t read_bytes=0;
  while((read_bytes=fread(frame.data(),1,frame.size(),stdin))>0){
    if(read_bytes!=frame.size()){fprintf(stderr,"incomplete RGBA frame\n");return 6;}
    source->ProcessData(frame.data(),w,h,w*4,gpupixel::GPUPIXEL_FRAME_TYPE_RGBA);
    auto rgba=sink->GetRgbaBuffer();
    if(!rgba||sink->GetWidth()!=w||sink->GetHeight()!=h)return 4;
    if(fwrite(rgba,1,frame.size(),out)!=frame.size())return 5;
    if(++count%30==0)fprintf(stderr,"processed %d frames\n",count);
  }
  if(ferror(stdin))return 7;
  if(fclose(out)!=0)return 8;
  fprintf(stderr,"finished %d frames\n",count);
  return 0;
}
